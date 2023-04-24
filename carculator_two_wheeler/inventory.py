"""
inventory.py contains Inventory which provides all methods to solve inventories.
"""

import numpy as np
from . import DATA_DIR
from carculator_utils.inventory import Inventory

np.warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

IAM_FILES_DIR = DATA_DIR / "IAM"


class InventoryTwoWheeler(Inventory):
    """
    Build and solve the inventory for results
    characterization and inventory export

    """

    def fill_in_A_matrix(self):
        """
        Fill-in the A matrix. Does not return anything. Modifies in place.
        Shape of the A matrix (values, products, activities).

        :param array: :attr:`array` from :class:`CarModel` class
        """

        # Glider/Frame
        idx = self.find_input_indices(("Two-wheeler, ", "Bicycle", "<25", "Human"))
        idx.extend(
            self.find_input_indices(("Two-wheeler, ", "Kick-scooter", "BEV"))
        )
        index = self.get_index_vehicle_from_array(
            [
                "Human",
            ],
            ["Bicycle <25"],
            method="and",
        )
        index.extend(
            self.get_index_vehicle_from_array(["BEV"], ["Kick-scooter"], method="and")
        )

        self.A[
            :,
            self.find_input_indices(
                contains=("bicycle production",), excludes=("battery",)
            ),
            idx,
        ] = (
            self.array[self.array_inputs["glider base mass"], :, index] * 1 / 17 * -1
        )

        idx = self.find_input_indices(
            contains=("Two-wheeler, ", "Bicycle", "BEV"), excludes=("cargo",)
        )
        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            ["Bicycle <25", "Bicycle <45"],
            method="and",
        )

        self.A[
            :,
            self.find_input_indices(
                ("electric bicycle production, without battery and motor",)
            ),
            idx,
        ] = (
            self.array[self.array_inputs["glider base mass"], :, index] * 1 / 17 * -1
        )

        idx = self.find_input_indices(
            contains=("Two-wheeler, ", "Bicycle", "BEV", "cargo")
        )
        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            ["Bicycle cargo"],
            method="and",
        )

        self.A[
            :,
            self.find_input_indices(
                ("electric cargo bicycle production, without battery and motor",)
            ),
            idx,
        ] = (
            self.array[self.array_inputs["glider base mass"], :, index] * 1 / 50 * -1
        )

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Moped", "ICEV"))
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "ICEV"))
        )
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "ICEV"))
        )
        index = self.get_index_vehicle_from_array(
            [
                "ICEV-p",
            ],
            [
                "Moped <4kW",
                "Scooter <4kW",
                "Scooter 4-11kW",
                "Motorcycle 4-11kW",
                "Motorcycle 11-35kW",
                "Motorcycle >35kW",
            ],
            method="and",
        )

        self.A[:, self.find_input_indices(("motor scooter production",)), idx,] = (
            self.array[self.array_inputs["glider base mass"], :, index] * 1 / 90 * -1
        )

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "BEV"))
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "ICEV"))
        )

        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            [
                "Scooter <4kW",
                "Scooter 4-11kW",
                "Motorcycle 4-11kW",
                "Motorcycle 11-35kW",
                "Motorcycle >35kW",
            ],
            method="and",
        )

        self.A[
            :,
            self.find_input_indices(("market for glider, for electric scooter",)),
            idx,
        ] = (
            self.array[self.array_inputs["glider base mass"], :, index] * -1
        )

        self.A[
            :,
            self.find_input_indices(contains=("Glider lightweighting",)),
            self.find_input_indices(contains=("Two-wheeler, ",)),
        ] = (
            self.array[self.array_inputs["lightweighting"], :]
            * self.array[self.array_inputs["glider base mass"], :]
        ) * -1

        self.A[
            :,
            self.find_input_indices(
                contains=("electric motor production, for electric scooter",)
            ),
            self.find_input_indices(contains=("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["electric engine mass"], :]) * -1

        self.A[
            :,
            self.find_input_indices(
                contains=("market for internal combustion engine, passenger car",)
            ),
            self.find_input_indices(contains=("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["combustion engine mass"], :]) * -1

        self.A[
            :,
            self.find_input_indices(
                contains=("powertrain production, for electric scooter",)
            ),
            self.find_input_indices(contains=("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["electrical powertrain mass"], :]) * -1

        self.A[
            :,
            self.find_input_indices(
                contains=("market for internal combustion engine, passenger car",)
            ),
            self.find_input_indices(contains=("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["mechanical powertrain mass"], :]) * -1

        # Powertrain components
        self.A[
            :,
            self.find_input_indices(("charger production, for electric scooter",)),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (
            self.array[self.array_inputs["charger mass"], :] * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for converter, for electric passenger car",)
            ),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (
            self.array[self.array_inputs["converter mass"], :] * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for inverter, for electric passenger car",)
            ),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (
            self.array[self.array_inputs["inverter mass"], :] * -1
        )

        self.A[
            :,
            self.find_input_indices(
                ("market for power distribution unit, for electric passenger car",)
            ),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (
            self.array[self.array_inputs["power distribution unit mass"], :] * -1
        )

        # Maintenance

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "ICEV"))
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "ICEV"))
        )

        index = self.get_index_vehicle_from_array(
            [
                "ICEV-p",
            ],
            [
                "Scooter <4kW",
                "Scooter 4-11kW",
                "Motorcycle 4-11kW",
                "Motorcycle 11-35kW",
                "Motorcycle >35kW",
            ],
            method="and",
        )

        self.A[:, self.find_input_indices(("maintenance, motor scooter",)), idx] = (
            self.array[self.array_inputs["lifetime kilometers"], :, index] / 25000 * -1
        )

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Bicycle <25", "Human"))
        index = self.get_index_vehicle_from_array(
            [
                "Human",
            ],
            [
                "Bicycle <25",
            ],
            method="and",
        )

        self.A[:, self.find_input_indices(("maintenance, bicycle",)), idx] = (
                self.array[self.array_inputs["lifetime kilometers"], :, index] / 25000 * -1
        )

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Bicycle", "BEV"))
        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            [
                "Bicycle <25",
                "Bicycle <45",
                "Bicycle cargo",
            ],
            method="and",
        )

        self.A[:, self.find_input_indices(("maintenance, electric bicycle, without battery",)), idx] = (
                self.array[self.array_inputs["lifetime kilometers"], :, index] / 25000 * -1
        )

        idx = self.find_input_indices(("Two-wheeler, ", "Kick-scooter", "BEV"))


        idx.extend(
            self.find_input_indices(("Two-wheeler, ", "Human, Bicycle <25"))
        )


        index = self.get_index_vehicle_from_array(["BEV"], ["Kick-scooter"], method="and")
        index.extend(
            self.get_index_vehicle_from_array(
                [
                    "Human",
                ],
                ["Bicycle <25"],
                method="and",
            )
        )


        self.A[:, self.find_input_indices(("treatment of used bicycle",)), idx] = (
                self.array[self.array_inputs["curb mass"], :, index] / 17
        )

        idx = self.find_input_indices(
            contains=("Two-wheeler, ", "Bicycle", "BEV")
        )
        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            ["Bicycle <25", "Bicycle <45", "Bicycle cargo"],
            method="and",
        )

        self.A[:, self.find_input_indices(("treatment of used electric bicycle",)), idx] = (
                self.array[self.array_inputs["curb mass"], :, index] / 24
        )

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "BEV"))
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "ICEV"))
        )
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "ICEV"))
        )
        idx.extend(
            self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "BEV"))
        )

        index = self.get_index_vehicle_from_array(
            [
                "BEV",
            ],
            [
                "Scooter <4kW",
                "Scooter 4-11kW",
                "Motorcycle 4-11kW",
                "Motorcycle 11-35kW",
                "Motorcycle >35kW",
            ],
            method="and",
        )
        index.extend(
            self.get_index_vehicle_from_array(
                ["ICEV-p"],
                [
                    "Scooter <4kW",
                    "Scooter 4-11kW",
                    "Motorcycle 4-11kW",
                    "Motorcycle 11-35kW",
                    "Motorcycle >35kW",
                ],
                method="and",
            )
        )

        idx = list(set(idx))

        self.A[:, self.find_input_indices(("manual dismantling of used electric scooter",)), idx] = (
                self.array[self.array_inputs["curb mass"], :, index] * -1
        )

        # Energy storage
        self.add_battery()

        index = self.get_index_vehicle_from_array(
            ["ICEV-p"]
        )

        self.A[
        :,
        self.find_input_indices(
            contains=("polyethylene production, high density, granulate",)
        ),
        self.find_input_indices(
            contains=("Two-wheeler, ", "ICEV-p")
        ),
        ] = (
                self.array[self.array_inputs["fuel tank mass"], :, index] * -1
        )

        # Chargers
        idx = self.find_input_indices(contains=("Two-wheeler, ", "Kick-scooter", "BEV"))
        self.A[:, self.find_input_indices(("charging station, 100W",)), idx] = -1

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Bicycle", "BEV"))
        self.A[:, self.find_input_indices(("charging station, 500W",)), idx] = -1

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Scooter", "BEV"))
        self.A[:, self.find_input_indices(("charging station, 3kW",)), idx] = -1

        idx = self.find_input_indices(contains=("Two-wheeler, ", "Motorcycle", "BEV"))
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
            self.find_input_indices(("market for transport, freight, sea, container ship",)),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["curb mass"]] / 1000 * 15900) * -1

        # 1'000 km by truck
        self.A[
            :,
            self.find_input_indices(("market group for transport, freight, lorry, unspecified",)),
            self.find_input_indices(("Two-wheeler, ",)),
        ] = (self.array[self.array_inputs["curb mass"]] / 1000 * 1000) * -1



        print("*********************************************************************")
