"""
inventory.py contains Inventory which provides all methods to solve inventories.
"""

import warnings

import numpy as np
from carculator_utils.inventory import Inventory

from . import DATA_DIR

warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

IAM_FILES_DIR = DATA_DIR / "IAM"


class InventoryTwoWheeler(Inventory):
    """
    Build and solve the inventory for results
    characterization and inventory export

    """

    def _select_vehicles(self, size_prefixes, powertrains):
        """Select foreground columns and model values in the same vehicle order.

        :param size_prefixes: Size-class prefixes, e.g. ``("Scooter", "Motorcycle")``.
        :param powertrains: Exact powertrain labels to include.
        :returns: Inventory column indices and the corresponding labelled array.
        """
        vehicles = [
            (size, powertrain)
            for size in self.scope["size"]
            if size.startswith(size_prefixes)
            for powertrain in self.scope["powertrain"]
            if powertrain in powertrains
        ]
        columns = [
            self.inputs[
                (
                    f"two-wheeler, {powertrain}, {size}",
                    self.vm.country,
                    "unit",
                    "two-wheeler",
                )
            ]
            for size, powertrain in vehicles
        ]
        labels = [f"{size} - {powertrain}" for size, powertrain in vehicles]
        return columns, self.array.sel(combined_dim=labels)

    def fill_in_A_matrix(self):
        """
        Fill-in the A matrix. Does not return anything. Modifies in place.
        Shape of the A matrix (values, products, activities).

        :param array: :attr:`array` from :class:`CarModel` class
        """

        # Glider/Frame
        idx = self.find_input_indices(
            ("two-wheeler, ", "Bicycle <25", "Human"), excludes=("transport",)
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("bicycle production",), excludes=("battery",)
            ),
            idx,
        ] = (
            self.array.sel(
                parameter="glider base mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(x in d for x in ["Bicycle <25", "Human"])
                ],
            )
            * 1
            / 17
            * -1
        )

        idx = self.find_input_indices(
            ("two-wheeler, ", "Kick-scooter", "BEV"), excludes=("transport",)
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("bicycle production",), excludes=("battery",)
            ),
            idx,
        ] = (
            self.array.sel(
                parameter="glider base mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(x in d for x in ["Kick-scooter", "BEV"])
                ],
            )
            * 1
            / 17
            * -1
        )

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle", "BEV"),
            excludes=("cargo", "transport"),
        )

        self.A[
            :,
            self.find_input_indices(
                ("electric bicycle production, without battery and motor",)
            ),
            idx,
        ] = (
            self.array.sel(
                parameter="glider base mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(x in d for x in ["Bicycle", "BEV"]) and "cargo" not in d
                ],
            )
            * 1
            / 17
            * -1
        )

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle", "BEV", "cargo"),
            excludes=("transport",),
        )

        self.A[
            :,
            self.find_input_indices(
                ("electric cargo bicycle production, without battery and motor",)
            ),
            idx,
        ] = (
            self.array.sel(
                parameter="glider base mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(x in d for x in ["Bicycle", "BEV", "cargo"])
                ],
            )
            * 1
            / 50
            * -1
        )

        idx, vehicles = self._select_vehicles(
            ("Moped", "Scooter", "Motorcycle"), ("ICEV-p",)
        )
        self.A[:, self.find_input_indices(("motor scooter production",)), idx] = (
            -vehicles.sel(parameter="glider base mass") / 90
        )

        idx, vehicles = self._select_vehicles(("Scooter", "Motorcycle"), ("BEV",))
        self.A[
            :,
            self.find_input_indices(("market for glider, for electric scooter",)),
            idx,
        ] = -vehicles.sel(parameter="glider base mass")

        self.A[
            :,
            self.find_input_indices(contains=("glider lightweighting",)),
            self.find_input_indices(
                contains=("two-wheeler, ",), excludes=("transport",)
            ),
        ] = (
            self.array.sel(parameter="lightweighting")
            * self.array.sel(parameter="glider base mass")
        ) * -1

        self.A[
            :,
            self.find_input_indices(
                contains=("electric motor production, for electric scooter",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="electric engine mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("market for internal combustion engine, passenger car",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="combustion engine mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("powertrain production, for electric scooter",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="electrical powertrain mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("market for internal combustion engine, passenger car",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="mechanical powertrain mass") * -1
        )

        # Powertrain components
        self.A[
            :,
            self.find_input_indices(("charger production, for electric scooter",)),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="charger mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for converter, for electric passenger car",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="converter mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for inverter, for electric passenger car",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="inverter mass") * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for power distribution unit, for electric passenger car",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="power distribution unit mass") * -1
        )

        # Maintenance

        idx, vehicles = self._select_vehicles(("Scooter", "Motorcycle"), ("ICEV-p",))
        self.A[:, self.find_input_indices(("maintenance, motor scooter",)), idx] = (
            -vehicles.sel(parameter="lifetime kilometers") / 25000
        )

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle <25", "Human"), excludes=("transport",)
        )

        self.A[:, self.find_input_indices(("maintenance, bicycle",)), idx] = (
            self.array.sel(
                parameter="lifetime kilometers",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(
                        x in d
                        for x in [
                            "Bicycle <25",
                            "Human",
                        ]
                    )
                ],
            )
            / 25000
            * -1
        )

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle", "BEV"), excludes=("transport",)
        )

        self.A[
            :,
            self.find_input_indices(
                ("maintenance, electric bicycle, without battery",)
            ),
            idx,
        ] = (
            self.array.sel(
                parameter="lifetime kilometers",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(
                        x in d
                        for x in [
                            "Bicycle",
                            "BEV",
                        ]
                    )
                ],
            )
            / 25000
            * -1
        )

        idx = self.find_input_indices(
            ("two-wheeler, ", "Kick-scooter", "BEV"), excludes=("transport",)
        )
        self.A[:, self.find_input_indices(("treatment of used bicycle",)), idx] = (
            self.array.sel(
                parameter="curb mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(
                        x in d
                        for x in [
                            "Kick-scooter",
                            "BEV",
                        ]
                    )
                ],
            )
            / 17
        )
        idx = self.find_input_indices(
            ("two-wheeler, ", "Human", "Bicycle <25"), excludes=("transport",)
        )

        self.A[:, self.find_input_indices(("treatment of used bicycle",)), idx] = (
            self.array.sel(
                parameter="curb mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(
                        x in d
                        for x in [
                            "Bicycle <25",
                            "Human",
                        ]
                    )
                ],
            )
            / 17
        )

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle", "BEV"), excludes=("transport",)
        )

        self.A[
            :, self.find_input_indices(("treatment of used electric bicycle",)), idx
        ] = (
            self.array.sel(
                parameter="curb mass",
                combined_dim=[
                    d
                    for d in self.array.coords["combined_dim"].values
                    if all(x in d for x in ["Bicycle", "BEV"])
                ],
            )
            / 24
        )

        idx, vehicles = self._select_vehicles(
            ("Scooter", "Motorcycle"), ("BEV", "ICEV-p")
        )
        self.A[
            :,
            self.find_input_indices(("manual dismantling of used electric scooter",)),
            idx,
        ] = -vehicles.sel(parameter="curb mass")

        # Energy storage
        self.add_battery()

        self.A[
            :,
            self.find_input_indices(
                contains=("polyethylene production, high density, granulate",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (
            self.array.sel(parameter="fuel tank mass")
            * (self.array.sel(parameter="combustion power") > 0)
            * -1
        )

        # Chargers
        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Kick-scooter", "BEV"), excludes=("transport",)
        )
        self.A[:, self.find_input_indices(("charging station, 100W",)), idx] = -1

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Bicycle", "BEV"), excludes=("transport",)
        )
        self.A[:, self.find_input_indices(("charging station, 500W",)), idx] = -1

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Scooter", "BEV"), excludes=("transport",)
        )
        self.A[:, self.find_input_indices(("charging station, 3kW",)), idx] = -1

        idx = self.find_input_indices(
            contains=("two-wheeler, ", "Motorcycle", "BEV"), excludes=("transport",)
        )
        self.A[:, self.find_input_indices(("charging station, 3kW",)), idx] = -1

        # END of vehicle building

        # Add vehicle dataset to transport dataset
        self.add_vehicle_to_transport_dataset()

        self.display_renewable_rate_in_mix()

        self.add_electricity_to_electric_vehicles()

        self.add_fuel_to_vehicles("petrol", ["ICEV-p"], "EV-p")

        self.add_abrasion_emissions()

        self.add_road_construction()

        self.add_road_maintenance()

        # reduce the burden from road maintenance
        # for bicycles and kick-scooter by half

        self.A[
            :,
            self.find_input_indices(("market for road maintenance",)),
            self.find_input_indices((f"transport, two-wheeler, ", "Kick-scooter")),
        ] *= 0.25

        self.A[
            :,
            self.find_input_indices(("market for road maintenance",)),
            self.find_input_indices((f"transport, two-wheeler, ", "Bicycle")),
        ] *= 0.5

        self.add_exhaust_emissions()

        self.add_noise_emissions()

        # Transport to market from China
        # 15'900 km by ship
        self.A[
            :,
            self.find_input_indices(
                ("market for transport, freight, sea, container ship",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (self.array.sel(parameter="curb mass") / 1000 * 15900) * -1

        # 1'000 km by truck
        self.A[
            :,
            self.find_input_indices(
                ("market group for transport, freight, lorry, unspecified",)
            ),
            [j for i, j in self.inputs.items() if i[0].startswith("two-wheeler, ")],
        ] = (self.array.sel(parameter="curb mass") / 1000 * 1000) * -1

        print("*********************************************************************")
