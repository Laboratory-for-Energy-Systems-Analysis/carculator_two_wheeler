from itertools import product
from pathlib import Path

import numexpr as ne
import numpy as np
import xarray as xr
import yaml
from carculator_utils.energy_consumption import EnergyConsumptionModel
from carculator_utils.model import VehicleModel


class TwoWheelerModel(VehicleModel):
    def set_all(self):
        """
        This method runs a series of other methods to obtain the tank-to-wheel energy requirement, efficiency
        of the car, costs, etc.

        :meth:`set_component_masses()`, :meth:`set_car_masses()` and :meth:`set_power_parameters()` are interdependent.
        `powertrain_mass` depends on `power`, `curb_mass` is affected by changes in `powertrain_mass`,
        `combustion engine mass` and `electric engine mass`, and `power` is a function of `curb_mass`.
        The current solution is to loop through the methods until the increment in driving mass is
        inferior to 0.1%.


        :returns: Does not return anything. Modifies ``self.array`` in place.

        """

        print("Building two-wheelers...")

        self.ecm = EnergyConsumptionModel(
            vehicle_type="two-wheeler",
            vehicle_size=list(self.array.coords["size"].values),
            powertrains=list(self.array.coords["powertrain"].values),
            cycle=self.cycle,
            gradient=self.gradient,
            country=self.country,
        )

        diff = 1.0
        while diff > 0.001:
            old_driving_mass = self["driving mass"].sum().values

            if self.target_mass:
                self.override_vehicle_mass()
            else:
                self.set_vehicle_masses()

            self.set_power_parameters()
            self.set_component_masses()
            self.set_battery_properties()
            self.set_energy_stored_properties()
            self.set_recuperation()

            # if user-provided values are passed,
            # they override the default values
            if "capacity" in self.energy_storage:
                self.override_battery_capacity()

            diff = (self["driving mass"].sum().values - old_driving_mass) / self[
                "driving mass"
            ].sum()

        if self.energy_consumption:
            self.override_ttw_energy()
        else:
            self.set_ttw_efficiency()
            self.calculate_ttw_energy()

        self.set_range()

        if self.target_range:
            self.override_range()
            self.set_energy_stored_properties()

        self.set_share_recuperated_energy()
        self.set_battery_fuel_cell_replacements()
        self.adjust_cost()

        self.set_electricity_consumption()
        self.set_costs()
        self.set_hot_emissions()
        self.set_particulates_emission()
        self.set_noise_emissions()

        self.remove_energy_consumption_from_unavailable_vehicles()

        print("Done!")

    def set_battery_chemistry(self):
        # override default values for batteries
        # if provided by the user
        self.energy_storage = {
            "electric": {
                x: "NMC-622"
                for x in product(
                    ["BEV"],
                    self.array.coords["size"].values,
                    self.array.year.values,
                )
            },
            "origin": "CN",
        }

    def adjust_cost(self):
        """
        This method adjusts costs of energy storage over time, to correct for the overly optimistic linear
        interpolation between years.

        """

        n_iterations = self.array.shape[-1]
        n_year = len(self.array.year.values)

        # If uncertainty is not considered, the cost factor equals 1.
        # Otherwise, a variability of +/-30% is added.

        if n_iterations == 1:
            cost_factor = 1
        else:
            if "reference" in self.array.value.values.tolist():
                cost_factor = np.ones((n_iterations, 1))
            else:
                cost_factor = np.random.triangular(0.7, 1, 1.3, (n_iterations, 1))

        # Correction of energy battery system cost, per kWh
        self.array.loc[
            :,
            [pt for pt in ["BEV"] if pt in self.array.coords["powertrain"].values],
            "energy battery cost per kWh",
            :,
            :,
        ] = np.reshape(
            (2.75e86 * np.exp(-9.61e-2 * self.array.year.values) + 5.059e1)
            * cost_factor,
            (1, 1, n_year, n_iterations),
        )

        # Correction of power battery system cost, per kW
        self.array.loc[
            :,
            [
                pt
                for pt in [
                    "ICEV-p",
                ]
                if pt in self.array.coords["powertrain"].values
            ],
            "power battery cost per kW",
            :,
            :,
        ] = np.reshape(
            (8.337e40 * np.exp(-4.49e-2 * self.array.year.values) + 11.17)
            * cost_factor,
            (1, 1, n_year, n_iterations),
        )

    def calculate_ttw_energy(self) -> None:
        """
        This method calculates the energy required to operate auxiliary services as well
        as to move the car. The sum is stored under the parameter label "TtW energy" in :attr:`self.array`.

        """

        self.energy = self.ecm.motive_energy_per_km(
            driving_mass=self["driving mass"],
            rr_coef=self["rolling resistance coefficient"],
            drag_coef=self["aerodynamic drag coefficient"],
            frontal_area=self["frontal area"],
            electric_motor_power=self["electric power"],
            engine_power=self["power"],
            recuperation_efficiency=self["recuperation efficiency"],
            aux_power=self["auxiliary power demand"],
            engine_efficiency=self["engine efficiency"],
            transmission_efficiency=self["transmission efficiency"],
            battery_charge_eff=self["battery charge efficiency"],
            battery_discharge_eff=self["battery discharge efficiency"],
        )

        self.energy = self.energy.assign_coords(
            {
                "powertrain": self.array.powertrain,
                "year": self.array.year,
                "size": self.array.coords["size"],
            }
        )

        distance = self.energy.sel(parameter="velocity").sum(dim="second") / 1000

        self["TtW energy"] = (
            self.energy.sel(
                parameter=[
                    "motive energy",
                    "auxiliary energy",
                ]
            ).sum(dim=["second", "parameter"])
            / distance
        ).T

        print(distance)

        self["TtW energy, combustion mode"] = self["TtW energy"] * (
            self["combustion power share"] > 0
        )
        self["TtW energy, electric mode"] = self["TtW energy"] * (
            self["combustion power share"] == 0
        )

        self["auxiliary energy"] = (
            self.energy.sel(parameter="auxiliary energy").sum(dim="second") / distance
        ).T

    def set_vehicle_masses(self):
        """
        Define ``curb mass``, ``driving mass``, and ``total cargo mass``.

            * `curb mass <https://en.wikipedia.org/wiki/Curb_weight>`__ is the mass of the vehicle and fuel, without people or cargo.
            * ``total cargo mass`` is the mass of the cargo and passengers.
            * ``driving mass`` is the ``curb mass`` plus ``total cargo mass``.

        .. note::
            driving mass = total cargo mass + driving mass

        """

        self["curb mass"] = self["glider base mass"] * (1 - self["lightweighting"])

        curb_mass_includes = [
            "fuel mass",
            "charger mass",
            "converter mass",
            "inverter mass",
            "power distribution unit mass",
            # Updates with set_components_mass
            "combustion engine mass",
            # Updates with set_components_mass
            "electric engine mass",
            # Updates with set_components_mass
            "mechanical powertrain mass",
            "electrical powertrain mass",
            "battery cell mass",
            "battery BoP mass",
            "fuel tank mass",
        ]
        self["curb mass"] += self[curb_mass_includes].sum(axis=2)

        self["total cargo mass"] = (
            self["average passengers"] * self["average passenger mass"]
            + self["cargo mass"]
        )
        self["driving mass"] = self["curb mass"] + self["total cargo mass"]

    def set_component_masses(self):
        self["combustion engine mass"] = (
            self["combustion power"] * self["combustion engine mass per power"]
        )
        self["electric engine mass"] = (
            self["electric power"] * self["electric engine mass per power"]
        ) * (self["electric power"] > 0)

        self["mechanical powertrain mass"] = (
            self["mechanical powertrain mass share"] * self["glider base mass"]
        ) - self["combustion engine mass"]

        self["electrical powertrain mass"] = (
            (self["electrical powertrain mass share"] * self["glider base mass"])
            - self["electric engine mass"]
            - self["charger mass"]
            - self["converter mass"]
            - self["inverter mass"]
            - self["power distribution unit mass"]
        )

    def set_battery_fuel_cell_replacements(self):
        """
        This methods calculates the number of replacement batteries needed
        to match the vehicle lifetime. Given the chemistry used,
        the cycle life is known. Given the lifetime kilometers and
        the kilometers per charge, the number of charge cycles can be inferred.

        If the battery lifetime surpasses the vehicle lifetime,
        100% of the burden of the battery production is allocated to the vehicle.
        Also, the number of replacement is rounded up.
        This means that the entirety of the battery replacement is allocated
        to the vehicle (and not to its potential second life).

        """
        # Number of replacement of battery is rounded *up*

        _ = lambda array: np.where(array == 0, 1, array)

        self["battery lifetime replacements"] = np.clip(
            (
                (self["lifetime kilometers"] * self["TtW energy"] / 3600)
                / _(self["electric energy stored"])
                / _(self["battery cycle life"])
                - 1
            ),
            1,
            3,
        ) * (self["charger mass"] > 0)

    def set_costs(self):
        self["glider cost"] = (
            self["glider base mass"] * self["glider cost slope"]
            + self["glider cost intercept"]
        )
        self["lightweighting cost"] = (
            self["glider base mass"]
            * self["lightweighting"]
            * self["glider lightweighting cost per kg"]
        )
        self["electric powertrain cost"] = (
            self["electric powertrain cost per kW"] * self["electric power"]
        )
        self["combustion powertrain cost"] = (
            self["combustion power"] * self["combustion powertrain cost per kW"]
        )
        self["power battery cost"] = (
            self["battery power"] * self["power battery cost per kW"]
        )
        self["energy battery cost"] = (
            self["energy battery cost per kWh"] * self["electric energy stored"]
        )

        self["fuel tank cost"] = self["fuel tank cost per kg"] * self["fuel mass"]
        # Per km
        self["energy cost"] = self["energy cost per kWh"] * self["TtW energy"] / 3600

        # For battery, need to divide cost of electricity in battery by efficiency of charging

        _ = lambda x: np.where(x == 0, 1, x)
        self["energy cost"] /= _(self["battery charge efficiency"])

        self["component replacement cost"] = (
            self["energy battery cost"] * self["battery lifetime replacements"]
        )

        with open(self.DATA_DIR / "purchase_cost_params.yaml", "r") as stream:
            to_markup = yaml.safe_load(stream)["markup"]

        to_markup = [m for m in to_markup if m in self.array.coords["parameter"].values]

        self[to_markup] *= self["markup factor"]

        # calculate costs per km:
        amortisation_factor = self["interest rate"] + (
            self["interest rate"]
            / (
                (np.array(1) + self["interest rate"]) ** self["lifetime kilometers"]
                - np.array(1)
            )
        )

        with open(self.DATA_DIR / "purchase_cost_params.yaml", "r") as stream:
            purchase_cost_list = yaml.safe_load(stream)["purchase"]

        purchase_cost_list = [
            m for m in purchase_cost_list if m in self.array.coords["parameter"].values
        ]

        self["purchase cost"] = self[purchase_cost_list].sum(axis=2)

        # per km
        self["amortised purchase cost"] = (
            self["purchase cost"] * amortisation_factor / self["kilometers per year"]
        )

        # per km
        self["maintenance cost"] = (
            self["maintenance cost per glider cost"]
            * self["glider cost"]
            / self["kilometers per year"]
        )

        # simple assumption that component replacement occurs at half of life.
        # simple assumption that component replacement
        # occurs at half of life.
        self["amortised component replacement cost"] = (
            (
                self["component replacement cost"]
                * (
                    (np.array(1) - self["interest rate"]) ** self["lifetime kilometers"]
                    / 2
                )
            )
            * amortisation_factor
            / self["kilometers per year"]
        )

        self["total cost per km"] = (
            self["energy cost"]
            + self["amortised purchase cost"]
            + self["maintenance cost"]
            + self["amortised component replacement cost"]
        )

    def calculate_cost_impacts(self, sensitivity=False, scope=None):
        """
        This method returns an array with cost values per vehicle-km, sub-divided into the following groups:

            * Purchase
            * Maintentance
            * Component replacement
            * Energy
            * Total cost of ownership

        :return: A xarray array with cost information per vehicle-km
        :rtype: xarray.core.dataarray.DataArray
        """

        if scope is None:
            scope = {
                "size": self.array.coords["size"].values.tolist(),
                "powertrain": self.array.coords["powertrain"].values.tolist(),
                "year": self.array.coords["year"].values.tolist(),
            }

        list_cost_cat = [
            "purchase",
            "maintenance",
            "component replacement",
            "energy",
            "total",
        ]

        response = xr.DataArray(
            np.zeros(
                (
                    len(scope["size"]),
                    len(scope["powertrain"]),
                    len(list_cost_cat),
                    len(scope["year"]),
                    len(self.array.coords["value"].values),
                )
            ),
            coords=[
                scope["size"],
                scope["powertrain"],
                ["purchase", "maintenance", "component replacement", "energy", "total"],
                scope["year"],
                self.array.coords["value"].values.tolist(),
            ],
            dims=["size", "powertrain", "cost_type", "year", "value"],
        )

        response.loc[
            :,
            :,
            ["purchase", "maintenance", "component replacement", "energy", "total"],
            :,
            :,
        ] = self.array.sel(
            powertrain=scope["powertrain"],
            size=scope["size"],
            year=scope["year"],
            parameter=[
                "amortised purchase cost",
                "maintenance cost",
                "amortised component replacement cost",
                "energy cost",
                "total cost per km",
            ],
        ).values

        if not sensitivity:
            return response
        else:
            return response / response.sel(value="reference")

    def remove_energy_consumption_from_unavailable_vehicles(self):
        """
        This method sets the energy consumption of vehicles that are not available to zero.
        """

        if "Human" in self.array.coords["powertrain"].values:
            sizes = [
                s
                for s in [
                    "Kick-scooter",
                    "Bicycle <45",
                    "Bicycle cargo",
                    "Moped <4kW",
                    "Scooter <4kW",
                    "Scooter 4-11kW",
                    "Motorcycle 4-11kW",
                    "Motorcycle 11-35kW",
                    "Motorcycle >35kW",
                ]
                if s in self.array.coords["size"].values
            ]

            self.array.loc[
                dict(
                    powertrain="Human",
                    size=sizes,
                    parameter="TtW energy",
                )
            ] = 0

        if "BEV" in self.array.coords["powertrain"].values:
            if "Moped <4kW" in self.array.coords["size"].values:
                self.array.loc[
                    dict(
                        powertrain="BEV",
                        size=[
                            "Moped <4kW",
                        ],
                        parameter="TtW energy",
                    )
                ] = 0

        if "ICEV-p" in self.array.coords["powertrain"].values:
            sizes = [
                s
                for s in [
                    "Kick-scooter",
                    "Bicycle <25",
                    "Bicycle <45",
                    "Bicycle cargo",
                ]
                if s in self.array.coords["size"].values
            ]

            self.array.loc[
                dict(
                    powertrain="ICEV-p",
                    size=sizes,
                    parameter="TtW energy",
                )
            ] = 0

        # set the `TtW energy` of BEV vehicles before 2010 to zero
        self.array.loc[
            dict(
                powertrain="BEV",
                year=slice(None, 2010),
                parameter="TtW energy",
            )
        ] = 0
