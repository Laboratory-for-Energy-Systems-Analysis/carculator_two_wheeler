"""Foreground purchases must follow vehicle labels across inventory scopes."""

import csv
import io
import warnings
from copy import deepcopy

import numpy as np
import pytest
import xarray as xr

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
    fill_xarray_from_input_parameters,
)

SIZES = ["Moped <4kW", "Scooter <4kW", "Motorcycle 11-35kW"]
SUPPLIERS = {
    "electric_glider": (
        "market for glider, for electric scooter",
        "GLO",
        "kilogram",
        "glider, for electric scooter",
    ),
    "petrol_glider": (
        "motor scooter production",
        "RER",
        "unit",
        "motor scooter, 50 cubic cm engine",
    ),
    "maintenance": (
        "maintenance, motor scooter",
        "CH",
        "unit",
        "maintenance, motor scooter",
    ),
    "dismantling": (
        "manual dismantling of used electric scooter",
        "GLO",
        "unit",
        "manual dismantling of electric scooter",
    ),
}


def expected_amounts(cell, size, powertrain):
    """Existing supplier scaling, evaluated for one exact vehicle selection."""
    glider = cell.sel(parameter="glider base mass")
    life = cell.sel(parameter="lifetime kilometers")
    curb = cell.sel(parameter="curb mass")
    amounts = {key: xr.zeros_like(glider) for key in SUPPLIERS}
    if powertrain == "ICEV-p":
        amounts["petrol_glider"] = glider / 90
        if size != "Moped <4kW":
            amounts["maintenance"] = life / 25000
    elif size != "Moped <4kW":
        amounts["electric_glider"] = glider
    if size != "Moped <4kW":
        # Retain the existing mass-scaled coefficient; this tests its recipient,
        # not the scientific validity of the dismantling dataset's scaling.
        amounts["dismantling"] = curb
    return amounts


@pytest.fixture(scope="module")
def completed():
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs,
        scope={"size": SIZES, "powertrain": ["BEV", "ICEV-p"], "year": [2025, 2030]},
    )
    array = array.sel(size=SIZES[::-1], year=[2030, 2025]).isel(value=[0, 0])
    array = array.assign_coords(value=["heavier", "reference"])
    array.loc[dict(parameter="glider base mass", value="heavier")] *= 1.2
    array.loc[dict(parameter="lifetime kilometers", value="heavier")] *= 1.4
    array.loc[dict(parameter="lifetime kilometers", year=2030)] *= 1.1
    original = array.copy(deep=True)
    model = TwoWheelerModel(array, country="CH")
    model.set_all()
    xr.testing.assert_identical(array, original)
    inventory = InventoryTwoWheeler(model, scenario="static", functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all()
    return model, inventory, impacts


def check_foreground(inventory):
    for size in inventory.scope["size"]:
        for pt in inventory.scope["powertrain"]:
            cell = inventory.vm.array.sel(size=size, powertrain=pt)
            if not bool((cell.sel(parameter="TtW energy") > 0).any()):
                continue
            column = inventory.inputs[
                (f"two-wheeler, {pt}, {size}", "CH", "unit", "two-wheeler")
            ]
            for label, expected in expected_amounts(cell, size, pt).items():
                row = inventory.inputs[SUPPLIERS[label]]
                np.testing.assert_allclose(
                    -inventory.A[:, row, column, :],
                    expected.transpose("value", "year"),
                    rtol=2e-6,
                    err_msg=f"{size}, {pt}, {label}",
                )


def test_completed_foreground_uses_each_vehicles_own_mass_and_lifetime(completed):
    _, inventory, _ = completed
    check_foreground(inventory)


@pytest.mark.parametrize(
    "size,powertrains",
    [
        ("Moped <4kW", ["ICEV-p"]),
        ("Scooter <4kW", ["BEV", "ICEV-p"]),
        ("Motorcycle 11-35kW", ["BEV", "ICEV-p"]),
        ("Scooter <4kW", ["BEV"]),
        ("Motorcycle 11-35kW", ["ICEV-p"]),
    ],
)
def test_individual_scope_matches_combined_impacts(completed, size, powertrains):
    model, _, impacts = completed
    selected = deepcopy(model)
    selected.array = model.array.sel(size=[size], powertrain=powertrains).copy(
        deep=True
    )
    original = selected.array.copy(deep=True)
    single = InventoryTwoWheeler(selected, scenario="static")
    check_foreground(single)
    xr.testing.assert_allclose(
        single.calculate_impacts(),
        impacts.sel(size=[size], powertrain=powertrains),
        rtol=2e-5,
        atol=1e-9,
    )
    xr.testing.assert_identical(selected.array, original)


def test_reordering_sizes_powertrains_and_samples_preserves_impacts(completed):
    model, _, impacts = completed
    reordered = deepcopy(model)
    order = {
        dim: list(model.array.coords[dim].values[::-1])
        for dim in ["size", "powertrain", "value"]
    }
    reordered.array = model.array.sel(order).copy(deep=True)
    inventory = InventoryTwoWheeler(reordered, scenario="static")
    check_foreground(inventory)
    xr.testing.assert_allclose(
        inventory.calculate_impacts(),
        impacts.sel(order),
        rtol=2e-5,
        atol=1e-9,
    )


@pytest.mark.parametrize("version", ["3.9", "3.10"])
def test_exports_keep_vehicle_specific_amounts_and_source_inventory(completed, version):
    pytest.importorskip("bw2io")
    model, _, _ = completed
    model = deepcopy(model)
    model.array = model.array.sel(value=["heavier"])
    inventory = InventoryTwoWheeler(model, scenario="static")
    matrix, indices = inventory.A.copy(), inventory.inputs.copy()
    original = model.array.copy(deep=True)
    impacts = inventory.calculate_impacts()
    expected_by_year = {}
    importers = inventory.export_lci(format="bw2io", ecoinvent_version=version)
    assert len(importers) == 2
    for year, importer in zip(model.array.year.values, importers):
        expected = {}
        for size in SIZES:
            for pt, exported_pt in [
                ("BEV", "battery electric"),
                ("ICEV-p", "gasoline"),
            ]:
                cell = model.array.sel(
                    size=size, powertrain=pt, year=year, value="heavier"
                )
                if cell.sel(parameter="TtW energy").item() == 0:
                    continue
                name = f"two-wheeler, {exported_pt}, {size}"
                (vehicle,) = [
                    a
                    for a in importer.data
                    if a["name"] == name
                    and a["location"] == "CH"
                    and a["unit"] == "unit"
                    and a["reference product"] == "two-wheeler"
                ]
                amounts = expected_amounts(cell, size, pt)
                for label, key in SUPPLIERS.items():
                    exchanges = [
                        e
                        for e in vehicle["exchanges"]
                        if (
                            e["name"],
                            e.get("location"),
                            e["unit"],
                            e.get("reference product"),
                        )
                        == key
                    ]
                    amount = amounts[label].item()
                    assert len(exchanges) == int(amount != 0)
                    if amount:
                        assert exchanges[0]["type"] == "technosphere"
                        assert exchanges[0]["amount"] == pytest.approx(amount, rel=2e-6)
                        expected[name.lower(), label] = amount
        expected_by_year[year] = expected
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*noise.*", category=UserWarning)
        csvs = inventory.export_lci(
            software="simapro", format="string", ecoinvent_version=version
        )
    assert len(csvs) == 2
    for year, content in zip(model.array.year.values, csvs):
        expected, actual = expected_by_year[year], {}
        section, vehicle = None, None
        for row in csv.reader(io.StringIO(content), delimiter=";"):
            if row == ["Process"]:
                section, vehicle = None, None
            elif not row or not row[0]:
                section = None
            elif len(row) == 1:
                section = row[0]
            elif section == "Products":
                matches = {
                    name for name, _ in expected if f"| {name} |" in row[0].lower()
                }
                assert len(matches) <= 1
                vehicle = next(iter(matches), None)
            elif section in ("Materials/fuels", "Waste to treatment") and vehicle:
                for label, key in SUPPLIERS.items():
                    if key[0] in row[0].lower():
                        assert (vehicle, label) not in actual
                        assert row[1] == ("kg" if key[2] == "kilogram" else "p")
                        assert section == (
                            "Waste to treatment"
                            if label == "dismantling"
                            else "Materials/fuels"
                        )
                        # SimaPro represents this waste service with the opposite
                        # sign to a Brightway technosphere input.
                        sign = -1 if section == "Waste to treatment" else 1
                        actual[vehicle, label] = sign * float(row[2])
        assert actual.keys() == expected.keys()
        for key, amount in expected.items():
            assert actual[key] == pytest.approx(amount, rel=2e-6)
    np.testing.assert_array_equal(inventory.A, matrix)
    assert inventory.inputs == indices
    xr.testing.assert_identical(model.array, original)
    xr.testing.assert_identical(inventory.calculate_impacts(), impacts)
