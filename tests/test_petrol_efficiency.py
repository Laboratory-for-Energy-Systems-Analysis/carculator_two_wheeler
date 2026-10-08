"""Regression checks for the restored petrol efficiency prior and its inventories."""

import json
from pathlib import Path

import numpy as np
import pytest
from carculator_utils.background_systems import BackgroundSystemModel

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

SIZES = [
    "Moped <4kW",
    "Scooter <4kW",
    "Scooter 4-11kW",
    "Motorcycle 4-11kW",
    "Motorcycle 11-35kW",
]
DATA = Path(package_file).parent / "data"


def test_restoration_preserves_metadata_and_relative_uncertainty():
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    provenance = json.loads((DATA / "petrol_efficiency_provenance.json").read_text())
    assert len(provenance["original_records"]) == 28
    for key, original in provenance["original_records"].items():
        record = defaults[key]
        assert record["powertrain"] == ["ICEV-p"]
        assert set(record["sizes"]) <= set(SIZES)
        expected = 0.18 * 1.004 ** max(0, record["year"] - 2020)
        if record["year"] == 2025:
            expected = (0.18 + 0.18 * 1.004**10) / 2
        assert record["amount"] == pytest.approx(expected)
        assert record["loc"] == pytest.approx(expected)
        assert record["minimum"] == pytest.approx(0.75 * expected)
        assert record["maximum"] == pytest.approx(1.25 * expected)
        for field in set(original) - {
            "amount",
            "loc",
            "minimum",
            "maximum",
            "source",
            "comment",
        }:
            assert record[field] == original[field]
    large = [
        r
        for r in defaults.values()
        if r.get("name") == "engine efficiency"
        and r.get("powertrain") == ["ICEV-p"]
        and "Motorcycle >35kW" in r["sizes"]
    ]
    assert large and all(r["amount"] == 0.24 for r in large)


@pytest.fixture(scope="module")
def completed_petrol_model():
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs,
        scope={"size": SIZES, "powertrain": ["ICEV-p"], "year": [2020, 2025, 2030]},
    )
    # Deterministic endpoints exercise each cell/sample independently.
    array = array.isel(value=[0, 0, 0]).assign_coords(value=[0, 1, 2])
    array.loc[dict(parameter="engine efficiency", value=0)] *= 0.75
    array.loc[dict(parameter="engine efficiency", value=2)] *= 1.25
    model = TwoWheelerModel(
        array,
        fuel_blend={
            "petrol": {
                "primary": {"type": "petrol", "share": [1, 0.7, 0]},
                "secondary": {
                    "type": "petrol - bioethanol - sugarbeet",
                    "share": [0, 0.3, 1],
                },
            }
        },
    )
    model.set_all()
    return model


def test_petrol_consumption_has_plausible_scale_and_efficiency_response(
    completed_petrol_model,
):
    model = completed_petrol_model
    fuel = model["fuel consumption"] * 100  # L/100 km
    # Broad default-case regression envelope, not a calibration accuracy target.
    assert np.isfinite(fuel).all()
    assert ((fuel > 0.5) & (fuel < 12)).all()
    assert (fuel.sel(value=0) > fuel.sel(value=1)).all()
    assert (fuel.sel(value=1) > fuel.sel(value=2)).all()
    # With fixed road load and no recuperation, fuel energy times efficiency is
    # shaft/auxiliary demand; these independent sample overrides preserve it.
    converted = model["TtW energy"] * model["engine efficiency"]
    np.testing.assert_allclose(
        converted.sel(value=0), converted.sel(value=2), rtol=2e-5
    )


def test_corrected_fuel_reaches_suppliers_and_tailpipe_carbon(completed_petrol_model):
    model = completed_petrol_model
    inventory = InventoryTwoWheeler(model, functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all()
    specs = BackgroundSystemModel().fuel_specs
    blend = model.fuel_blend["petrol"]
    (market,) = inventory.find_input_indices(("fuel supply for petrol vehicles",))
    lhv = sum(c["share"] * specs[c["type"]]["lhv"] for c in blend.values())
    for component in blend.values():
        supplier = inventory.inputs[tuple(specs[component["type"]]["name"])]
        np.testing.assert_allclose(
            -inventory.A[:, supplier, market, :],
            np.broadcast_to(component["share"], (3, 3)),
            atol=1e-8,
        )
    for size in SIZES:
        (column,) = inventory.find_input_indices(
            (f"transport, {model.vehicle_type}, ", ", ICEV-p,", size)
        )
        energy = (
            model["TtW energy"]
            .sel(size=size, powertrain="ICEV-p")
            .transpose("value", "year")
            .values
        )
        expected_mass = energy / (lhv * 1000)  # kJ/km / (MJ/kg * 1000)
        np.testing.assert_allclose(
            -inventory.A[:, market, column, :],
            expected_mass,
            rtol=2e-5,
        )
        for biogenic, label in ((False, "fossil"), (True, "non-fossil")):
            carbon = sum(
                c["share"]
                * specs[c["type"]]["co2"]
                * (
                    specs[c["type"]]["biogenic_share"]
                    if biogenic
                    else 1 - specs[c["type"]]["biogenic_share"]
                )
                for c in blend.values()
            )
            row = inventory.inputs[(f"Carbon dioxide, {label}", ("air",), "kilogram")]
            np.testing.assert_allclose(
                -inventory.A[:, row, column, :],
                expected_mass * carbon,
                rtol=2e-5,
                atol=1e-9,
            )
