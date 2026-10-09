"""Completed BEV scenarios must couple pack sizing, mass, energy and inventory."""

from copy import deepcopy

import numpy as np
import pytest
import xarray as xr
from carculator_utils.numerical import ConvergenceError

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
    fill_xarray_from_input_parameters,
)

CHEMISTRIES = ["LFP", "NMC-111", "NMC-622", "NMC-811"]
SIZES = ["Bicycle <25", "Scooter <4kW", "Motorcycle 11-35kW"]


def inputs(sizes=("Scooter <4kW",), years=(2025,), powertrains=("BEV",), samples=False):
    parameters = TwoWheelerInputParameters()
    parameters.static()
    _, array = fill_xarray_from_input_parameters(
        parameters,
        scope={
            "size": list(sizes),
            "powertrain": list(powertrains),
            "year": list(years),
        },
    )
    if samples:
        array = array.isel(value=[0, 0]).assign_coords(value=["reference", "loaded"])
        array.loc[dict(parameter="cargo mass", value="loaded")] += 30
    return array


def run(array, **kwargs):
    model = TwoWheelerModel(array, **kwargs)
    model.set_all()
    return model


def assert_balanced(model):
    np.testing.assert_allclose(
        model["electric energy stored"],
        model["energy battery mass"]
        * model["battery cell mass share"]
        * model["battery cell energy density"],
        rtol=1e-6,
    )
    # Sum physical components independently of the sizing-loop state.
    parts = [
        "fuel mass",
        "charger mass",
        "converter mass",
        "inverter mass",
        "power distribution unit mass",
        "combustion engine mass",
        "electric engine mass",
        "mechanical powertrain mass",
        "electrical powertrain mass",
        "fuel tank mass",
        "battery cell mass",
        "battery BoP mass",
    ]
    expected_curb = model["glider base mass"] * (1 - model["lightweighting"])
    for part in parts:
        expected_curb = expected_curb + model[part]
    np.testing.assert_allclose(model["curb mass"], expected_curb, rtol=1e-5)
    expected_driving = (
        expected_curb
        + model["cargo mass"]
        + model["average passengers"] * model["average passenger mass"]
    )
    np.testing.assert_allclose(model["driving mass"], expected_driving, rtol=1e-5)
    # Re-evaluate energy at the final component-derived mass, without re-sizing.
    frozen = deepcopy(model)
    frozen["driving mass"] = expected_driving
    frozen.calculate_ttw_energy()
    np.testing.assert_allclose(model["TtW energy"], frozen["TtW energy"], rtol=1e-5)
    np.testing.assert_allclose(
        model["range"],
        model["electric energy stored"]
        * model["battery DoD"]
        * 3600
        / frozen["TtW energy"],
        rtol=1e-5,
    )


def assert_inventory_consistent(model, chemistry):
    inventory = InventoryTwoWheeler(model, scenario="static", functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all()
    electricity_rows = inventory.find_input_indices(
        ("electricity supply for electric vehicles",)
    )
    (battery_row,) = inventory.find_input_indices(
        (f"market for battery, Li-ion, {chemistry.replace('-', '')}",)
    )
    for size in model.array.coords["size"].values:
        (transport_col,) = inventory.find_input_indices(
            ("transport, two-wheeler,", "BEV", size)
        )
        (electricity_row,) = inventory.get_vehicle_supply_indices(
            "electricity supply for electric vehicles", [transport_col]
        )
        (vehicle_col,) = inventory.find_input_indices(
            ("two-wheeler,", "BEV", size), excludes=("transport",)
        )
        selection = dict(size=size, powertrain="BEV")
        expected_grid = (
            (
                model["TtW energy"]
                / 3600
                / model["battery charge efficiency"]
                / model["charger efficiency"]
            )
            .sel(**selection)
            .transpose("value", "year")
        )
        expected_pack = (
            (
                model["energy battery mass"]
                * (1 + model["battery lifetime replacements"])
            )
            .sel(**selection)
            .transpose("value", "year")
        )
        np.testing.assert_allclose(
            -inventory.A[:, electricity_row, transport_col, :], expected_grid, rtol=1e-6
        )
        np.testing.assert_allclose(
            -inventory.A[:, electricity_rows, transport_col, :].sum(axis=1),
            expected_grid,
            rtol=1e-6,
        )
        np.testing.assert_allclose(
            -inventory.A[:, battery_row, vehicle_col, :], expected_pack, rtol=1e-6
        )


@pytest.mark.parametrize("chemistry", CHEMISTRIES)
def test_range_converges_across_sizes_years_samples_and_inventories(chemistry):
    array = inputs(sizes=SIZES, years=(2020, 2025, 2030), samples=True)
    original = array.copy(deep=True)
    keys = [("BEV", size, year) for size in SIZES for year in [2020, 2025, 2030]]
    storage = {"electric": dict.fromkeys(keys, chemistry)}
    target = dict.fromkeys(keys, 150)
    original_storage = deepcopy(storage)
    model = run(array, energy_storage=storage, target_range=target)
    xr.testing.assert_identical(array, original)
    assert storage == original_storage
    assert target == dict.fromkeys(keys, 150)
    np.testing.assert_allclose(model["range"], 150, rtol=1e-6)
    assert_balanced(model)
    assert (
        model["TtW energy"].sel(value="loaded")
        > model["TtW energy"].sel(value="reference")
    ).all()
    assert_inventory_consistent(model, chemistry)


@pytest.mark.parametrize("chemistry", CHEMISTRIES)
def test_range_solution_matches_fresh_capacity_run(chemistry):
    array = inputs()
    key = ("BEV", "Scooter <4kW", 2025)
    storage = {"electric": {key: chemistry}}
    ranged = run(array, energy_storage=storage, target_range={key: 200})
    storage["capacity"] = {key: ranged["electric energy stored"].item()}
    fixed = run(array, energy_storage=storage)
    for parameter in [
        "range",
        "power",
        "driving mass",
        "TtW energy",
        "electricity consumption",
    ]:
        np.testing.assert_allclose(ranged[parameter], fixed[parameter], rtol=1e-5)


@pytest.mark.parametrize("direction,levels", [("capacity", [2, 4]), ("mass", [10, 25])])
@pytest.mark.parametrize("chemistry", ["LFP", "NMC-811"])
def test_capacity_and_mass_changes_reach_consumption_range_and_inventory(
    direction, levels, chemistry
):
    models = []
    keys = [("BEV", size, 2025) for size in SIZES]
    for level in levels:
        array = inputs(sizes=SIZES)
        storage = {"electric": dict.fromkeys(keys, chemistry)}
        if direction == "capacity":
            storage["capacity"] = dict.fromkeys(keys, level)
        else:
            array.loc[dict(parameter="energy battery mass")] = level
        model = run(array, energy_storage=storage)
        fixed = (
            "electric energy stored"
            if direction == "capacity"
            else "energy battery mass"
        )
        np.testing.assert_allclose(model[fixed], level, rtol=1e-6)
        assert_balanced(model)
        assert_inventory_consistent(model, chemistry)
        models.append(model)
    for parameter in [
        "energy battery mass",
        "electric energy stored",
        "curb mass",
        "TtW energy",
        "range",
        "electricity consumption",
    ]:
        assert (models[1][parameter] > models[0][parameter]).all(), parameter


@pytest.mark.parametrize(
    "fixed", [None, "target_mass", "energy_consumption", "capacity"]
)
def test_chemistry_feedback_and_fixed_constraints(fixed):
    array = inputs()
    key = ("BEV", "Scooter <4kW", 2025)
    models = []
    for chemistry in ["LFP", "NMC-811"]:
        storage = {"electric": {key: chemistry}}
        overrides = {}
        if fixed == "capacity":
            storage["capacity"] = {key: 1}
        elif fixed:
            overrides[fixed] = {key: 100 if fixed == "target_mass" else 90}
        model = run(array, energy_storage=storage, target_range={key: 200}, **overrides)
        assert_balanced(model)
        np.testing.assert_allclose(model["range"], 200, rtol=1e-6)
        if fixed == "target_mass":
            np.testing.assert_allclose(model["curb mass"], 100)
        elif fixed == "energy_consumption":
            np.testing.assert_allclose(model["TtW energy"], 90, rtol=1e-6)
        elif fixed == "capacity":
            reference = run(
                array,
                energy_storage={"electric": {key: chemistry}},
                target_range={key: 200},
            )
            np.testing.assert_allclose(
                model["electric energy stored"],
                reference["electric energy stored"],
                rtol=1e-5,
            )
        models.append(model)
    assert (
        models[0]["energy battery mass"].item()
        > models[1]["energy battery mass"].item()
    )
    for parameter in ["TtW energy", "electric energy stored"]:
        if fixed in ["target_mass", "energy_consumption"]:
            np.testing.assert_allclose(
                models[0][parameter], models[1][parameter], rtol=1e-6
            )
        else:
            assert models[0][parameter].item() > models[1][parameter].item()


def test_overrides_are_scoped_and_none_targets_preserve_results():
    array = inputs(
        sizes=("Bicycle <25", "Scooter <4kW"),
        years=(2020, 2025),
        powertrains=("BEV", "ICEV-p", "Human"),
    )
    key = ("BEV", "Scooter <4kW", 2025)
    storage = {"capacity": {("BEV", "Scooter <4kW", 2020): 2}}
    baseline = run(array, energy_storage=storage)
    ranged = run(array, energy_storage=storage, target_range={key: 200})
    for size in array.coords["size"].values:
        for powertrain in array.powertrain.values:
            for year in array.year.values:
                if (powertrain, size, year) != key:
                    selection = dict(powertrain=powertrain, size=size, year=year)
                    xr.testing.assert_allclose(
                        ranged.array.sel(**selection),
                        baseline.array.sel(**selection),
                        rtol=1e-5,
                    )
    none = run(array, energy_storage=storage, target_range={key: None})
    xr.testing.assert_identical(none.array, baseline.array)


@pytest.mark.parametrize("override", ["target_mass", "energy_consumption"])
def test_fixed_constraints_also_work_without_a_range_target(override):
    key = ("BEV", "Scooter <4kW", 2025)
    model = run(inputs(), **{override: {key: 100}})
    parameter = "curb mass" if override == "target_mass" else "TtW energy"
    np.testing.assert_allclose(model[parameter], 100, rtol=1e-6)
    assert_balanced(model)


def test_sizing_limit_raises_with_vehicle_coordinates():
    key = ("BEV", "Scooter <4kW", 2025)
    with pytest.raises(ConvergenceError, match="iteration limit.*Scooter <4kW"):
        run(inputs(), target_range={key: 200}, max_iterations=1)


def test_range_feedback_covers_all_available_bev_sizes():
    parameters = TwoWheelerInputParameters()
    parameters.static()
    _, array = fill_xarray_from_input_parameters(
        parameters, scope={"powertrain": ["BEV"], "year": [2025]}
    )
    array = array.sel(
        size=[size for size in array.coords["size"].values if size != "Moped <4kW"]
    )
    targets = {("BEV", size, 2025): 100 for size in array.coords["size"].values}
    model = run(array, target_range=targets)
    np.testing.assert_allclose(model["range"], 100, rtol=1e-6)
    assert_balanced(model)
    assert_inventory_consistent(model, "NMC-811")


def test_range_sizing_preserves_availability_masks():
    array = inputs(sizes=("Scooter <4kW", "Moped <4kW"), years=(2010, 2025))
    model = run(array, target_range={("BEV", "Scooter <4kW", 2025): 100})
    for parameter in ["TtW energy", "electricity consumption"]:
        assert (model[parameter].sel(year=2010) == 0).all()
        assert (model[parameter].sel(size="Moped <4kW") == 0).all()
        assert model[parameter].sel(size="Scooter <4kW", year=2025).item() > 0


def test_partial_fixed_constraints_preserve_unselected_vehicles():
    array = inputs(sizes=SIZES, years=(2020, 2025))
    baseline = run(array)
    key = ("BEV", "Scooter <4kW", 2025)
    model = run(
        array,
        target_range={key: 200},
        target_mass={key: 100},
        energy_consumption={key: 90},
    )
    assert_balanced(model)
    for size in SIZES:
        for year in [2020, 2025]:
            if ("BEV", size, year) != key:
                selection = dict(size=size, year=year)
                xr.testing.assert_allclose(
                    model.array.sel(**selection),
                    baseline.array.sel(**selection),
                    rtol=1e-5,
                )


def test_capacity_precedes_input_pack_mass():
    key = ("BEV", "Scooter <4kW", 2025)
    models = []
    for mass in [10, 30]:
        array = inputs()
        array.loc[dict(parameter="energy battery mass")] = mass
        models.append(run(array, energy_storage={"capacity": {key: 4}}))
    xr.testing.assert_allclose(models[0].array, models[1].array, rtol=1e-5)
