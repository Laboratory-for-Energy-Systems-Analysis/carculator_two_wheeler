"""Default equipment scope and explicit cost overrides on completed two-wheelers."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from carculator_two_wheeler import TwoWheelerInputParameters, TwoWheelerModel
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
DEFAULTS = json.loads((DATA / "default_parameters.json").read_text())
PROVENANCE = json.loads((DATA / "heat_pump_cost_provenance.json").read_text())
SIZES = [s for s in PROVENANCE["scope"]["sizes"] if s != "Moped <4kW"]
YEARS = [2020, 2025, 2030]
CHANGED_OUTPUTS = [
    "heat pump cost",
    "purchase cost",
    "amortised purchase cost",
    "total cost per km",
]


@pytest.mark.parametrize("sampled", [False, True])
def test_heat_pump_defaults_are_zero_including_sampling_and_interpolation(sampled):
    records = {k: v for k, v in DEFAULTS.items() if v["name"] == "heat pump cost"}
    assert set(records) == set(PROVENANCE["original_records"])
    for key, record in records.items():
        old = PROVENANCE["original_records"][key]
        for field in ("name", "sizes", "powertrain", "year"):
            assert record[field] == old[field]
        assert record["amount"] == record["loc"] == 0
        assert record["uncertainty_type"] == 1
        assert "minimum" not in record and "maximum" not in record
    inputs = TwoWheelerInputParameters()
    if sampled:
        inputs.stochastic(16, seed=481)
    else:
        inputs.static()
    _, array = fill_xarray_from_input_parameters(inputs)
    costs = array.sel(parameter="heat pump cost").interp(year=range(2000, 2051))
    assert np.isfinite(costs).all()
    assert (costs == 0).all()


def complete(defaults, array_override=False):
    inputs = TwoWheelerInputParameters(parameters=defaults)
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": SIZES, "powertrain": ["BEV"], "year": YEARS}
    )
    # Integer lifetime allows an independent discounted-cash-flow calculation.
    array.loc[dict(parameter="lifetime kilometers")] = 10 * array.sel(
        parameter="kilometers per year"
    )
    if array_override:
        array.loc[dict(parameter="heat pump cost", year=2025)] = 175.25
    original = array.copy(deep=True)
    model = TwoWheelerModel(array)
    model.set_all()
    xr.testing.assert_identical(array, original)
    return model


@pytest.fixture(scope="module")
def default_model():
    return complete(DEFAULTS)


def check_cost_delta(baseline, changed, expected):
    # No physics or other cost component is allowed to compensate for this charge.
    xr.testing.assert_identical(
        baseline.array.drop_sel(parameter=CHANGED_OUTPUTS),
        changed.array.drop_sel(parameter=CHANGED_OUTPUTS),
    )
    np.testing.assert_allclose(
        changed["heat pump cost"] - baseline["heat pump cost"], expected, rtol=0, atol=0
    )
    np.testing.assert_allclose(
        changed["purchase cost"] - baseline["purchase cost"],
        expected,
        rtol=1e-5,
        atol=0.002,
    )
    repayments = 1 / sum((1 + baseline["interest rate"]) ** -t for t in range(1, 11))
    expected_per_km = expected * repayments / baseline["kilometers per year"]
    for parameter in ("amortised purchase cost", "total cost per km"):
        np.testing.assert_allclose(
            changed[parameter] - baseline[parameter],
            expected_per_km,
            rtol=2e-5,
            atol=2e-7,
        )


def test_removing_default_charge_reduces_purchase_once_without_markup(default_model):
    previous = copy.deepcopy(DEFAULTS)
    previous.update(copy.deepcopy(PROVENANCE["original_records"]))
    old_model = complete(previous)
    check_cost_delta(
        default_model, old_model, xr.full_like(default_model["heat pump cost"], 300)
    )


@pytest.mark.parametrize("source", ["array", "dictionary"])
def test_explicit_heat_pump_cost_survives_complete_model(default_model, source):
    parameters = copy.deepcopy(DEFAULTS)
    if source == "dictionary":
        for record in parameters.values():
            if record["name"] == "heat pump cost" and record["year"] == 2025:
                record["amount"] = record["loc"] = 175.25
    before = copy.deepcopy(parameters)
    model = complete(parameters, array_override=source == "array")
    assert parameters == before
    expected = xr.zeros_like(default_model["heat pump cost"])
    expected.loc[dict(year=2025)] = 175.25
    check_cost_delta(default_model, model, expected)
