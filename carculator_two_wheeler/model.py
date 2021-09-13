import numexpr as ne
import numpy as np
import xarray as xr

from .energy_consumption import EnergyConsumptionModel
from .hot_emissions import HotEmissionsModel
from .noise_emissions import NoiseEmissionsModel


def finite(array, mask_value=0):
    return np.where(np.isfinite(array), array, mask_value)


class TwoWheelerModel:

    """
    This class represents the entirety of the vehicles considered, with useful attributes, such as an array that stores
    all the vehicles parameters.

    :ivar array: multi-dimensional numpy-like array that contains parameters' value(s)
    :vartype array: xarray.DataArray
    :ivar mappings: Dictionary with names correspondence
    :vartype mappings: dict
    :ivar ecm: instance of :class:`EnergyConsumptionModel` class for a given driving cycle
    :vartype ecm: coarse.energy_consumption.EnergyConsumptionModel

    """

    def __init__(self, array, gradient=None, energy_storage=None):

        self.array = array

        self.ecm = EnergyConsumptionModel(size=self.array.coords["size"].values)
        self.energy_storage = energy_storage or {
            "electric": {"BEV": "NMC-111", "PHEV-e": "NMC-111", "FCEV": "NMC-111"}
        }

        if "BEV" in self.array.powertrain.values:
            with self("BEV") as cpm:
                if "BEV" in self.energy_storage["electric"]:
                    cpm["battery cell energy density"] = cpm[
                        "battery cell energy density, "
                        + self.energy_storage["electric"]["BEV"]
                    ]
                else:
                    cpm["battery cell energy density"] = cpm[
                        "battery cell energy density, NMC-111"
                    ]

    def __call__(self, key):
        """
        This method fixes a dimension of the `array` attribute given a powertrain technology selected.

        Set up this class as a context manager, so we can have some nice syntax

        .. code-block:: python

            with class('some powertrain') as cpm:
                cpm['something']. # Will be filtered for the correct powertrain

        On with block exit, this filter is cleared
        https://stackoverflow.com/a/10252925/164864

        :param key: A powertrain type, e.g., "FCEV"
        :type key: str
        :return: An instance of `array` filtered after the powertrain selected.

        """
        self.__cache = self.array
        self.array = self.array.sel(powertrain=key)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.array = self.__cache
        del self.__cache

    def __getitem__(self, key):
        """
        Make class['foo'] automatically filter for the parameter 'foo'
        Makes the model code much cleaner

        :param key: Parameter name
        :type key: str
        :return: `array` filtered after the parameter selected
        """

        return self.array.sel(parameter=key)

    def __setitem__(self, key, value):
        self.array.loc[{"parameter": key}] = value

    # Make it easier/more flexible to filter by powertrain types
    def __getattr__(self, key):
        if key in self.mappings:
            return self.mappings[key]

    def set_all(self, drop_hybrids=True, electric_utility_factor=None):
        """
        This method runs a series of other methods to obtain the tank-to-wheel energy requirement, efficiency
        of the car, costs, etc.

        :meth:`set_component_masses()`, :meth:`set_car_masses()` and :meth:`set_power_parameters()` are interdependent.
        `powertrain_mass` depends on `power`, `curb_mass` is affected by changes in `powertrain_mass`,
        `combustion engine mass` and `electric engine mass`, and `power` is a function of `curb_mass`.
        The current solution is to loop through the methods until the increment in driving mass is
        inferior to 0.1%.

        :param drop_hybrids: boolean. True by default. If False, the underlying vehicles used to build plugin-hybrid
                vehicles remain present in the array.
        :param electric_utility_factor: array. If an array is passed, its values are used to override the
                electric utility factor for plugin hybrid vehicles. If not, this factor is calculated using a relation
                described in `set_electric_utility_factor()`

        :returns: Does not return anything. Modifies ``self.array`` in place.

        """

        print("Building two-wheelers...")

        diff = 1.0
        while diff > 0.01:
            old_driving_mass = self["driving mass"].sum().values
            self.set_car_masses()

            self.set_power_parameters()
            self.set_component_masses()
            self.set_battery_properties()
            self.set_battery_replacements()
            self.set_recuperation()
            self.calculate_ttw_energy()
            self.set_energy_stored_properties()

            diff = (self["driving mass"].sum().values - old_driving_mass) / self[
                "driving mass"
            ].sum()

        self.adjust_cost()
        self.set_range()
        self.set_electricity_consumption()
        self.set_costs()
        self.set_hot_emissions()
        self.set_noise_emissions()

        # we remove vehicles that are not available for the specified years
        # we remove all electric vehicles from before 2010
        self.array.loc[dict(parameter="is_available")] = 1
        l_years = [y for y in self.array.coords["year"].values if y < 2010]
        if len(l_years) > 0 and "BEV" in self.array.powertrain.values:
            self.array.loc[
                dict(parameter="is_available", year=l_years, powertrain="BEV")
            ] = 0

        if "Human" in self.array.powertrain.values:
            if any(
                s in self.array.coords["size"].values
                for s in [
                    "Bicycle <45",
                    "Bicycle cargo",
                    "Scooter <4kW",
                    "Moped <4kW",
                    "Scooter 4-11kW",
                    "Motorcycle 4-11kW",
                    "Motorcycle 11-35kW",
                    "Motorcycle >35kW",
                ]
            ):
                self.array.loc[
                    dict(
                        parameter="is_available",
                        powertrain="Human",
                        size=[
                            s
                            for s in [
                                "Bicycle <45",
                                "Bicycle cargo",
                                "Scooter <4kW",
                                "Moped <4kW",
                                "Scooter 4-11kW",
                                "Motorcycle 4-11kW",
                                "Motorcycle 11-35kW",
                                "Motorcycle >35kW",
                            ]
                            if s in self.array.coords["size"].values
                        ],
                    )
                ] = 0

        if (
            "Moped <4kW" in self.array.coords["size"].values
            and "BEV" in self.array.powertrain.values
        ):
            self.array.loc[
                dict(
                    parameter="is_available",
                    powertrain="BEV",
                    size=[
                        "Moped <4kW",
                    ],
                )
            ] = 0

        if any(p in self.array.powertrain.values for p in ["Human", "ICEV-p"]):
            if "Kick-scooter" in self.array.coords["size"].values:
                self.array.loc[
                    dict(
                        parameter="is_available",
                        powertrain=[
                            p
                            for p in ["Human", "ICEV-p"]
                            if p in self.array.powertrain.values
                        ],
                        size=[
                            "Kick-scooter",
                        ],
                    )
                ] = 0

        if "ICEV-p" in self.array.powertrain.values:
            if any(
                s in self.array.coords["size"].values
                for s in [
                    "Kick-scooter",
                    "Bicycle <25",
                    "Bicycle <45",
                    "Bicycle cargo",
                ]
            ):
                self.array.loc[
                    dict(
                        parameter="is_available",
                        powertrain=["ICEV-p"],
                        size=[
                            s
                            for s in [
                                "Kick-scooter",
                                "Bicycle <25",
                                "Bicycle <45",
                                "Bicycle cargo",
                            ]
                            if s in self.array.coords["size"].values
                        ],
                    )
                ] = 0

        print("Done!")

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

    def set_electricity_consumption(self):
        """
        This method calculates the total electricity consumption for BEV and plugin-hybrid vehicles
        :returns: Does not return anything. Modifies ``self.array`` in place.
        """

        if "BEV" in self.array.coords["powertrain"].values:
            with self("BEV") as cpm:
                cpm["electricity consumption"] = (
                    cpm["TtW energy"] / cpm["battery charge efficiency"]
                ) / 3600

    def calculate_ttw_energy(self):
        """
        This method calculates the energy required to operate auxiliary services as well
        as to move the car. The sum is stored under the parameter label "TtW energy" in :attr:`self.array`.

        """
        self.energy = xr.DataArray(
            np.zeros(
                (
                    len(self.array.coords["size"]),
                    len(self.array.coords["powertrain"]),
                    5,
                    len(self.array.coords["year"]),
                    len(self.array.coords["value"]),
                    self.ecm.cycle.shape[0],
                )
            ).astype("float32"),
            coords=[
                self.array.coords["size"],
                self.array.coords["powertrain"],
                [
                    "auxiliary energy",
                    "motive energy",
                    "motive energy at wheels",
                    "recuperated energy",
                    "recuperated energy at wheels",
                ],
                self.array.coords["year"],
                self.array.coords["value"],
                np.arange(self.ecm.cycle.shape[0]),
            ],
            dims=["size", "powertrain", "parameter", "year", "value", "second"],
        )

        motive_power, recuperated_power, distance = self.ecm.motive_energy_per_km(
            driving_mass=self["driving mass"],
            rr_coef=self["rolling resistance coefficient"],
            drag_coef=self["aerodynamic drag coefficient"],
            frontal_area=self["frontal area"],
            recuperation_efficiency=self["recuperation efficiency"],
            motor_power=self["electric power"],
        )

        self.energy.loc[dict(parameter="motive energy at wheels")] = np.clip(
            motive_power.T, 0, self["power"].values[..., None]
        )

        self.energy.loc[dict(parameter="recuperated energy at wheels")] = (
            np.clip(recuperated_power.T, 0, self["electric power"].values[..., None])
            * -1
        )

        self.energy.loc[dict(parameter="auxiliary energy")] = np.where(
            self.energy.loc[dict(parameter="motive energy at wheels")] > 0,
            self.array.sel(parameter="auxiliary power demand").values[..., None] / 1000,
            0,
        )

        self["TtW efficiency"] = (
            self["transmission efficiency"]
            * self["engine efficiency"]
            * self["battery discharge efficiency"]
        )

        self.energy.loc[dict(parameter="motive energy")] = np.clip(
            self.energy.loc[dict(parameter="motive energy at wheels")]
            / self["TtW efficiency"],
            0,
            self["power"].values[..., None],
        )

        # a round trip from and to the wheels has to be accounted for
        self.energy.loc[dict(parameter="recuperated energy")] = np.clip(
            (
                self.energy.loc[dict(parameter="recuperated energy at wheels")]
                * (
                    self["transmission efficiency"]
                    * self["engine efficiency"]
                    * self["battery charge efficiency"]
                    * self["battery discharge efficiency"]
                    * self["engine efficiency"]
                    * self["transmission efficiency"]
                )
            ),
            self["electric power"].values[..., None] * -1,
            0,
        )

        self.energy = self.energy.fillna(0)
        self.energy *= np.isfinite(self.energy)

        self["TtW energy"] = (
            self.energy.sel(
                parameter=["motive energy", "auxiliary energy", "recuperated energy"]
            )
            .sum(dim=["second", "parameter"])
            .T
            / distance
        ).T

        self["auxiliary energy"] = (
            self.energy.sel(parameter="auxiliary energy").sum(dim="second").T / distance
        ).T

    def set_recuperation(self):
        self["recuperation efficiency"] = (
            self["transmission efficiency"]
            * self["battery charge efficiency"]
            * self["braking energy recuperation"]
        )

    def set_battery_replacements(self):
        """
        This methods calculates the fraction of the replacement battery needed to match the vehicle lifetime.


        """
        # Number of replacement of battery is rounded *up*

        for pt in [
            pwt for pwt in ["BEV"] if pwt in self.array.coords["powertrain"].values
        ]:
            with self(pt) as cpm:
                battery_tech_label = (
                    "battery cycle life, " + self.energy_storage["electric"][pt]
                )
                cpm["battery lifetime replacements"] = finite(
                    np.ceil(
                        np.clip(
                            (
                                # number of charge cycles needed divided by the expected cycle life
                                (
                                    cpm["lifetime kilometers"]
                                    * (cpm["TtW energy"] / 3600)
                                )
                                / cpm["electric energy stored"]
                                / cpm[battery_tech_label]
                            )
                            - 1,
                            1,
                            None,
                        )
                    )
                )

    def set_car_masses(self):
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
            "electric charger mass",
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

    def set_power_parameters(self):
        """Set electric and combustion motor powers based on input parameter ``power to mass ratio``."""
        # Convert from W/kg to kW
        self["power"] = self["power to mass ratio"] * self["curb mass"] / 1000
        self["combustion power share"] = self["combustion power share"].clip(
            min=0, max=1
        )
        self["combustion power"] = self["power"] * self["combustion power share"]
        self["electric power"] = self["power"] * (1 - self["combustion power share"])

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
            - self["electric charger mass"]
            - self["converter mass"]
            - self["inverter mass"]
            - self["power distribution unit mass"]
        )

    def set_battery_properties(self):
        pt_list = [
            pt for pt in ["ICEV-p"] if pt in self.array.coords["powertrain"].values
        ]
        self.array.loc[:, pt_list, "battery power"] = self.array.loc[
            :, pt_list, "electric power"
        ]

        self.array.loc[:, pt_list, "battery cell mass"] = (
            self.array.loc[:, pt_list, "battery power"]
            / self.array.loc[:, pt_list, "battery cell power density"]
        )

        self["battery cell mass share"] = self["battery cell mass share"].clip(
            min=0, max=1
        )
        self.array.loc[:, pt_list, "battery BoP mass", :, :] = (
            self.array.loc[
                :,
                pt_list,
                "battery cell mass",
            ]
            * (1 - self.array.loc[:, pt_list, "battery cell mass share", :, :])
        )

        list_pt_el = [
            pt for pt in ["BEV"] if pt in self.array.coords["powertrain"].values
        ]

        self.array.loc[:, list_pt_el, "battery cell mass"] = (
            self.array.loc[:, list_pt_el, "energy battery mass"]
            * self.array.loc[:, list_pt_el, "battery cell mass share"]
        )

        self.array.loc[:, list_pt_el, "battery BoP mass"] = self.array.loc[
            :, list_pt_el, "energy battery mass"
        ] * (1 - self.array.loc[:, list_pt_el, "battery cell mass share"])

    def set_range(self):

        list_pt = [
            pt for pt in ["ICEV-p"] if pt in self.array.coords["powertrain"].values
        ]

        list_pt_el = [
            pt for pt in ["BEV"] if pt in self.array.coords["powertrain"].values
        ]

        fuel_mass = self.array.loc[:, list_pt, "fuel mass"]
        lhv = self.array.loc[:, list_pt, "LHV fuel MJ per kg"]

        energy_stored = self.array.loc[:, list_pt_el, "electric energy stored"]
        battery_DoD = self.array.loc[:, list_pt_el, "battery DoD"]

        TtW_el = self.array.loc[:, list_pt_el, "TtW energy"]
        TtW = self.array.loc[:, list_pt, "TtW energy"]

        self.array.loc[:, list_pt, "range"] = ne.evaluate(
            "(fuel_mass * lhv * 1000) / TtW"
        )
        self.array.loc[:, list_pt_el, "range"] = ne.evaluate(
            "(energy_stored * battery_DoD * 3.6 * 1000) / TtW_el"
        )

    def set_energy_stored_properties(self):

        list_combustion = [
            pt for pt in ["ICEV-p"] if pt in self.array.coords["powertrain"].values
        ]

        self.array.loc[:, list_combustion, "oxidation energy stored"] = (
            self.array.loc[:, list_combustion, "fuel mass"]
            * self.array.loc[:, list_combustion, "LHV fuel MJ per kg"]
            / 3.6
        )

        # fuel tank mass as a share of the fuel mass
        self.array.loc[:, list_combustion, "fuel tank mass"] = (
            self.array.loc[:, list_combustion, "fuel mass"]
            * self.array.loc[:, list_combustion, "fuel tank mass share"]
        )

        if "BEV" in self.array.coords["powertrain"].values:
            with self("BEV") as cpm:

                cpm["electric energy stored"] = (
                    cpm["battery cell mass"] * cpm["battery cell energy density"]
                )

        # kWh electricity/kg battery cell
        self["battery cell production energy electricity share"] = self[
            "battery cell production energy electricity share"
        ].clip(min=0, max=1)
        self["battery cell production electricity"] = (
            self["battery cell production energy"]
            * self["battery cell production energy electricity share"]
        )
        # MJ heat/kg battery cell
        self["battery cell production heat"] = (
            self["battery cell production energy"]
            - self["battery cell production electricity"]
        ) * 3.6

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

        if "BEV" in self.array.coords["powertrain"].values:
            with self("BEV"):
                self["energy cost"] /= self["battery charge efficiency"]

        self["component replacement cost"] = (
            self["energy battery cost"] * self["battery lifetime replacements"]
        )

        to_markup = [
            "combustion powertrain cost",
            "component replacement cost",
            "electric powertrain cost",
            "energy battery cost",
            "fuel tank cost",
            "glider cost",
            "lightweighting cost",
            "power battery cost",
        ]

        self[to_markup] *= self["markup factor"]

        # calculate costs per km:
        self["lifetime"] = self["lifetime kilometers"] / self["kilometers per year"]
        i = self["interest rate"]
        lifetime = self["lifetime"]
        amortisation_factor = ne.evaluate("i + (i / ((1 + i) ** lifetime - 1))")

        purchase_cost_list = [
            "battery onboard charging infrastructure cost",
            "combustion exhaust treatment cost",
            "combustion powertrain cost",
            "electric powertrain cost",
            "energy battery cost",
            "fuel tank cost",
            "glider cost",
            "heat pump cost",
            "lightweighting cost",
            "power battery cost",
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
        km_per_year = self["kilometers per year"]
        com_repl_cost = self["component replacement cost"]
        self["amortised component replacement cost"] = ne.evaluate(
            "(com_repl_cost * ((1 - i) ** lifetime / 2) * amortisation_factor / km_per_year)"
        )

        self["total cost per km"] = (
            self["energy cost"]
            + self["amortised purchase cost"]
            + self["maintenance cost"]
            + self["amortised component replacement cost"]
        )

    def set_hot_emissions(self):
        """
        Calculate hot pollutant emissions based on ``driving cycle``.
        The driving cycle is passed to the :class:`HotEmissionsModel` class and :meth:`get_emissions_per_powertrain`
        return emissions per substance per second of driving cycle.
        :return: Does not return anything. Modifies ``self.array`` in place.
        """
        hem = HotEmissionsModel(self.ecm.cycle)

        list_direct_emissions = [
            "Carbon monoxide direct emissions, urban",
            "Nitrogen oxides direct emissions, urban",
            "NMVOC direct emissions, urban",
            "Particulate matters direct emissions, urban",
            "Methane direct emissions, urban",
            "Ammonia direct emissions, urban",
            "Dinitrogen oxide direct emissions, urban",
            "Ethane direct emissions, urban",
            "Propane direct emissions, urban",
            "Butane direct emissions, urban",
            "Pentane direct emissions, urban",
            "Hexane direct emissions, urban",
            "Cyclohexane direct emissions, urban",
            "Heptane direct emissions, urban",
            "Ethene direct emissions, urban",
            "Propene direct emissions, urban",
            "1-Pentene direct emissions, urban",
            "Toluene direct emissions, urban",
            "m-Xylene direct emissions, urban",
            "o-Xylene direct emissions, urban",
            "Formaldehyde direct emissions, urban",
            "Acetaldehyde direct emissions, urban",
            "Benzaldehyde direct emissions, urban",
            "Acetone direct emissions, urban",
            "Methyl ethyl ketone direct emissions, urban",
            "Acrolein direct emissions, urban",
            "Styrene direct emissions, urban",
            "PAH, polycyclic aromatic hydrocarbons direct emissions, urban",
            "Arsenic direct emissions, urban",
            "Selenium direct emissions, urban",
            "Zinc direct emissions, urban",
            "Copper direct emissions, urban",
            "Nickel direct emissions, urban",
            "Chromium direct emissions, urban",
            "Chromium VI direct emissions, urban",
            "Mercury direct emissions, urban",
            "Cadmium direct emissions, urban",
            "Benzene direct emissions, urban",
            "Carbon monoxide direct emissions, suburban",
            "Nitrogen oxides direct emissions, suburban",
            "NMVOC direct emissions, suburban",
            "Particulate matters direct emissions, suburban",
            "Methane direct emissions, suburban",
            "Ammonia direct emissions, suburban",
            "Dinitrogen oxide direct emissions, suburban",
            "Ethane direct emissions, suburban",
            "Propane direct emissions, suburban",
            "Butane direct emissions, suburban",
            "Pentane direct emissions, suburban",
            "Hexane direct emissions, suburban",
            "Cyclohexane direct emissions, suburban",
            "Heptane direct emissions, suburban",
            "Ethene direct emissions, suburban",
            "Propene direct emissions, suburban",
            "1-Pentene direct emissions, suburban",
            "Toluene direct emissions, suburban",
            "m-Xylene direct emissions, suburban",
            "o-Xylene direct emissions, suburban",
            "Formaldehyde direct emissions, suburban",
            "Acetaldehyde direct emissions, suburban",
            "Benzaldehyde direct emissions, suburban",
            "Acetone direct emissions, suburban",
            "Methyl ethyl ketone direct emissions, suburban",
            "Acrolein direct emissions, suburban",
            "Styrene direct emissions, suburban",
            "PAH, polycyclic aromatic hydrocarbons direct emissions, suburban",
            "Arsenic direct emissions, suburban",
            "Selenium direct emissions, suburban",
            "Zinc direct emissions, suburban",
            "Copper direct emissions, suburban",
            "Nickel direct emissions, suburban",
            "Chromium direct emissions, suburban",
            "Chromium VI direct emissions, suburban",
            "Mercury direct emissions, suburban",
            "Cadmium direct emissions, suburban",
            "Benzene direct emissions, suburban",
            "Carbon monoxide direct emissions, rural",
            "Nitrogen oxides direct emissions, rural",
            "NMVOC direct emissions, rural",
            "Particulate matters direct emissions, rural",
            "Methane direct emissions, rural",
            "Ammonia direct emissions, rural",
            "Dinitrogen oxide direct emissions, rural",
            "Ethane direct emissions, rural",
            "Propane direct emissions, rural",
            "Butane direct emissions, rural",
            "Pentane direct emissions, rural",
            "Hexane direct emissions, rural",
            "Cyclohexane direct emissions, rural",
            "Heptane direct emissions, rural",
            "Ethene direct emissions, rural",
            "Propene direct emissions, rural",
            "1-Pentene direct emissions, rural",
            "Toluene direct emissions, rural",
            "m-Xylene direct emissions, rural",
            "o-Xylene direct emissions, rural",
            "Formaldehyde direct emissions, rural",
            "Acetaldehyde direct emissions, rural",
            "Benzaldehyde direct emissions, rural",
            "Acetone direct emissions, rural",
            "Methyl ethyl ketone direct emissions, rural",
            "Acrolein direct emissions, rural",
            "Styrene direct emissions, rural",
            "PAH, polycyclic aromatic hydrocarbons direct emissions, rural",
            "Arsenic direct emissions, rural",
            "Selenium direct emissions, rural",
            "Zinc direct emissions, rural",
            "Copper direct emissions, rural",
            "Nickel direct emissions, rural",
            "Chromium direct emissions, rural",
            "Chromium VI direct emissions, rural",
            "Mercury direct emissions, rural",
            "Cadmium direct emissions, rural",
            "Benzene direct emissions, rural",
        ]

        l_y = []
        for y in self.array.year.values:
            # European emission standards function of registration year
            if y < 2003:
                l_y.append(1)
            if 2003 <= y < 2006:
                l_y.append(2)
            if 2006 <= y < 2016:
                l_y.append(3)
            if 2017 <= y < 2020:
                l_y.append(4)
            if y >= 2020:
                l_y.append(5)

        if "ICEV-p" in self.array.powertrain.values:
            sizes = [
                s
                for s in self.array.coords["size"].values
                if s
                not in ["Bicycle <25", "Bicycle <45", "Bicycle cargo", "Kick-scooter"]
            ]

            self.array.loc[
                dict(powertrain="ICEV-p", parameter=list_direct_emissions, size=sizes)
            ] = hem.get_hot_emissions(
                powertrain_type="ICEV-p",
                euro_class=l_y,
                sizes=sizes,
                energy_consumption=self.energy.sel(
                    powertrain="ICEV-p",
                    parameter=[
                        "motive energy",
                        "auxiliary energy",
                        "recuperated energy",
                    ],
                    size=sizes,
                ).sum(dim="parameter"),
            )

    def set_noise_emissions(self):
        """
        Calculate noise emissions based on ``driving cycle``.
        The driving cycle is passed to the :class:`NoiseEmissionsModel` class and :meth:`get_sound_power_per_compartment`
        returns emissions per compartment type ("rural", "non-urban" and "urban") per second of driving cycle.

        Noise emissions are not differentiated by size classes at the moment, but only by powertrain "type"
        (e.g., combustion, hybrid and electric)

        :return: Does not return anything. Modifies ``self.array`` in place.
        """

        sizes = [
            s
            for s in self.array.coords["size"].values
            if s not in ["Kick-scooter", "Bicycle <25", "Bicycle <45", "Bicycle cargo"]
        ]

        if len(sizes) > 0:

            nem = NoiseEmissionsModel(sizes=sizes)

            list_noise_emissions = [
                "noise, octave 1, day time, urban",
                "noise, octave 2, day time, urban",
                "noise, octave 3, day time, urban",
                "noise, octave 4, day time, urban",
                "noise, octave 5, day time, urban",
                "noise, octave 6, day time, urban",
                "noise, octave 7, day time, urban",
                "noise, octave 8, day time, urban",
                "noise, octave 1, day time, suburban",
                "noise, octave 2, day time, suburban",
                "noise, octave 3, day time, suburban",
                "noise, octave 4, day time, suburban",
                "noise, octave 5, day time, suburban",
                "noise, octave 6, day time, suburban",
                "noise, octave 7, day time, suburban",
                "noise, octave 8, day time, suburban",
                "noise, octave 1, day time, rural",
                "noise, octave 2, day time, rural",
                "noise, octave 3, day time, rural",
                "noise, octave 4, day time, rural",
                "noise, octave 5, day time, rural",
                "noise, octave 6, day time, rural",
                "noise, octave 7, day time, rural",
                "noise, octave 8, day time, rural",
            ]

            if "ICEV-p" in self.array.powertrain.values:

                self.array.loc[
                    dict(
                        powertrain="ICEV-p", size=sizes, parameter=list_noise_emissions
                    )
                ] = nem.get_sound_power_per_compartment("combustion").T[
                    :, :, None, None
                ]

            if "BEV" in self.array.powertrain.values:

                self.array.loc[
                    dict(powertrain="BEV", size=sizes, parameter=list_noise_emissions)
                ] = nem.get_sound_power_per_compartment("electric").T[:, :, None, None]

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
