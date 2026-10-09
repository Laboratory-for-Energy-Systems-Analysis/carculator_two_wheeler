"""Replacement fractions must reach completed battery inventories and costs."""

import numpy as np
import pytest
import xarray as xr

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
    fill_xarray_from_input_parameters,
)


def inputs(sizes=None, years=(2025,), powertrains=("BEV",)):
    parameters = TwoWheelerInputParameters()
    parameters.static()
    scope = {"powertrain": list(powertrains), "year": list(years)}
    if sizes is not None:
        scope["size"] = list(sizes)
    return fill_xarray_from_input_parameters(parameters, scope=scope)[1]


def check_inventory(model, expected_replacements):
    inventory = InventoryTwoWheeler(model, scenario="static", functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all()
    (disposal_row,) = inventory.find_input_indices(("market for used Li-ion battery",))
    electricity_rows = inventory.find_input_indices(
        ("electricity supply for electric vehicles",)
    )
    for size in model.array.coords["size"].values:
        (vehicle_col,) = inventory.find_input_indices(
            ("two-wheeler,", "BEV", size), excludes=("transport",)
        )
        (transport_col,) = inventory.find_input_indices(
            ("transport, two-wheeler,", "BEV", size)
        )
        (electricity_row,) = inventory.get_vehicle_supply_indices(
            "electricity supply for electric vehicles", [transport_col]
        )
        for year_index, year in enumerate(model.array.year.values):
            selection = dict(size=size, powertrain="BEV", year=year)
            chemistry = model.energy_storage["electric"][("BEV", size, year)]
            (battery_row,) = inventory.find_input_indices(
                (f"market for battery, Li-ion, {chemistry.replace('-', '')}",)
            )
            pack = model["energy battery mass"].sel(**selection).values.ravel()
            expected_supply = pack * (1 + expected_replacements)
            np.testing.assert_allclose(
                -inventory.A[:, battery_row, vehicle_col, year_index],
                expected_supply,
                rtol=2e-6,
            )
            np.testing.assert_allclose(
                inventory.A[:, disposal_row, vehicle_col, year_index],
                expected_supply,
                rtol=2e-6,
            )
            grid = (
                model["TtW energy"]
                / 3600
                / model["battery charge efficiency"]
                / model["charger efficiency"]
            )
            np.testing.assert_allclose(
                -inventory.A[:, electricity_row, transport_col, year_index],
                grid.sel(**selection).values.ravel(),
                rtol=2e-6,
            )
            np.testing.assert_allclose(
                -inventory.A[:, electricity_rows, transport_col, year_index].sum(
                    axis=1
                ),
                grid.sel(**selection).values.ravel(),
                rtol=2e-6,
            )


def test_default_bevs_do_not_force_an_extra_pack_in_any_modern_year():
    array = inputs(years=(2020, 2025, 2030))
    array = array.sel(
        size=[s for s in array.coords["size"].values if s != "Moped <4kW"]
    )
    before = array.copy(deep=True)
    model = TwoWheelerModel(array)
    model.set_all()
    xr.testing.assert_identical(array, before)
    # Independently establish that throughput fits in the first pack.
    lifetime_kwh = model["lifetime kilometers"] * model["TtW energy"] / 3600
    first_pack_throughput = (
        model["electric energy stored"] * model["battery cycle life"]
    )
    assert (lifetime_kwh < first_pack_throughput).all()
    for parameter in [
        "battery lifetime replacements",
        "component replacement cost",
        "amortised component replacement cost",
    ]:
        assert (model[parameter] == 0).all(), parameter
    check_inventory(model, 0)


@pytest.mark.parametrize("depth_of_discharge", [0.5, 0.9])
def test_fractional_multiple_and_capped_replacements_balance_costs_and_inventories(
    depth_of_discharge,
):
    # 2 kWh * 1,000 equivalent full cycles = 2,000 kWh per pack life.
    # At 90 kJ/km (0.025 kWh/km), one pack life corresponds to 80,000 km.
    # Keep the established fractional allocation and three-replacement cap.
    lifetime_km = np.array([20000, 80000, 120000, 160000, 240000, 400000])
    expected = np.array([0, 0, 0.5, 1, 2, 3])
    labels = ["reference", "one_life", "half_extra", "one_extra", "two_extra", "capped"]
    array = (
        inputs(sizes=("Scooter <4kW",))
        .isel(value=[0] * len(labels))
        .assign_coords(value=labels)
    )
    array.loc[dict(parameter="lifetime kilometers")] = xr.DataArray(
        lifetime_km, dims="value", coords={"value": labels}
    )
    array.loc[dict(parameter="kilometers per year")] = (
        array.sel(parameter="lifetime kilometers") / 10
    )
    array.loc[dict(parameter="battery cycle life, NMC-811")] = 1000
    array.loc[dict(parameter="battery DoD")] = depth_of_discharge
    array.loc[dict(parameter="interest rate")] = 0.05
    array.loc[dict(parameter="markup factor")] = 1.2
    key = ("BEV", "Scooter <4kW", 2025)
    model = TwoWheelerModel(
        array, energy_storage={"capacity": {key: 2}}, energy_consumption={key: 90}
    )
    model.set_all()
    np.testing.assert_allclose(
        model["battery lifetime replacements"].values.ravel(),
        expected,
        rtol=2e-6,
        atol=1e-6,
    )
    # The reference retail markup applies once to replacement purchases too.
    unit_cost = model["energy battery cost per kWh"].values.ravel()
    replacement_cost = 2 * unit_cost * expected * 1.2
    np.testing.assert_allclose(
        model["component replacement cost"].values.ravel(),
        replacement_cost,
        rtol=2e-6,
        atol=1e-4,
    )
    repayments = sum(1.05**-year for year in range(1, 11))
    replacement_per_km = replacement_cost / 1.05**5 / repayments / (lifetime_km / 10)
    np.testing.assert_allclose(
        model["amortised component replacement cost"].values.ravel(),
        replacement_per_km,
        rtol=2e-6,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        model["total cost per km"],
        model["amortised purchase cost"]
        + model["maintenance cost"]
        + model["energy cost"]
        + model["amortised component replacement cost"],
        rtol=2e-6,
    )
    check_inventory(model, expected)


def test_human_and_petrol_scopes_still_have_no_energy_battery_replacements():
    array = inputs(
        sizes=("Bicycle <25", "Scooter <4kW"), powertrains=("Human", "ICEV-p")
    )
    model = TwoWheelerModel(array)
    model.set_all()
    assert (model["battery lifetime replacements"] == 0).all()
    assert (model["component replacement cost"] == 0).all()
