"""Scoped charger prior, sampled bounds and completed cost accounting."""

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
PROVENANCE = json.loads(
    (DATA / "kick_scooter_charger_cost_provenance.json").read_text()
)
PARAMETER = "battery onboard charging infrastructure cost"
SIZES = ["Kick-scooter", "Bicycle <25", "Scooter <4kW", "Motorcycle >35kW"]
YEARS = [2020, 2025, 2030]
CHANGED = [PARAMETER, "purchase cost", "amortised purchase cost", "total cost per km"]


def test_kick_scooter_prior_has_unique_scope_and_documented_bounds():
    for key, old in PROVENANCE["original_records"].items():
        remainder = DEFAULTS[key]
        assert "Kick-scooter" not in remainder["sizes"]
        assert set(remainder["sizes"]) <= set(old["sizes"]) - {"Kick-scooter"}
        assert {k: v for k, v in remainder.items() if k != "sizes"} == {
            k: v for k, v in old.items() if k != "sizes"
        }
        matching = [
            r
            for r in DEFAULTS.values()
            if r["name"] == PARAMETER
            and r["year"] == old["year"]
            and "Kick-scooter" in r["sizes"]
            and "BEV" in r["powertrain"]
        ]
        assert len(matching) == 1
        record = matching[0]
        assert record["sizes"] == ["Kick-scooter"]
        assert record["powertrain"] == ["BEV"]
        assert record["uncertainty_type"] == 5
        assert record["amount"] == record["loc"] == 70
        assert record["minimum"] == 40
        assert record["maximum"] == 100


@pytest.mark.parametrize("sampled", [False, True])
def test_charger_prior_is_bounded_through_native_and_interpolated_years(sampled):
    inputs = TwoWheelerInputParameters()
    if sampled:
        inputs.stochastic(32, seed=173)
    else:
        inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": ["Kick-scooter"], "powertrain": ["BEV"]}
    )
    costs = array.sel(parameter=PARAMETER).interp(year=range(2000, 2051))
    assert np.isfinite(costs).all()
    if sampled:
        assert (costs >= 40).all() and (costs <= 100).all()
        assert costs.sel(year=2025).std().item() > 0
    else:
        assert (costs == 70).all()


def complete(parameters, charger=None, legacy=False, array_override=False):
    inputs = TwoWheelerInputParameters(parameters=parameters)
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": SIZES, "powertrain": ["BEV"], "year": YEARS}
    )
    # Ten years permits an independent sum of discounted annual repayments.
    array.loc[dict(parameter="lifetime kilometers")] = 10 * array.sel(
        parameter="kilometers per year"
    )
    if legacy:
        for old in PROVENANCE["original_records"].values():
            if old["year"] in YEARS:
                array.loc[
                    dict(parameter=PARAMETER, size="Kick-scooter", year=old["year"])
                ] = old["amount"]
    if charger is not None:
        array.loc[dict(parameter=PARAMETER, size="Kick-scooter")] = charger
    if array_override:
        array.loc[dict(parameter=PARAMETER, size="Kick-scooter", year=2025)] = 123.45
    before = array.copy(deep=True)
    model = TwoWheelerModel(array)
    model.set_all()
    xr.testing.assert_identical(array, before)
    return model


@pytest.fixture(scope="module")
def legacy_model():
    return complete(DEFAULTS, legacy=True)


def check_cost_change(before, after):
    xr.testing.assert_identical(
        before.array.drop_sel(parameter=CHANGED),
        after.array.drop_sel(parameter=CHANGED),
    )
    # Other classes retain every input and output, including cost components.
    xr.testing.assert_identical(
        before.array.sel(size=SIZES[1:]), after.array.sel(size=SIZES[1:])
    )
    delta = after[PARAMETER] - before[PARAMETER]
    np.testing.assert_allclose(
        after["purchase cost"] - before["purchase cost"], delta, rtol=1e-5, atol=0.001
    )
    repayment = 1 / sum((1 + before["interest rate"]) ** -t for t in range(1, 11))
    per_km = delta * repayment / before["kilometers per year"]
    for parameter in ("amortised purchase cost", "total cost per km"):
        np.testing.assert_allclose(
            after[parameter] - before[parameter], per_km, rtol=2e-5, atol=2e-7
        )
    assert (after["purchase cost"] > 0).all()
    assert (after["total cost per km"] > 0).all()


@pytest.mark.parametrize("charger", [40, 70, 100])
def test_complete_runs_at_charger_bounds_apply_cost_once_without_markup(
    legacy_model, charger
):
    model = complete(DEFAULTS, charger=charger)
    assert (model[PARAMETER].sel(size="Kick-scooter") == charger).all()
    check_cost_change(legacy_model, model)


@pytest.mark.parametrize("source", ["array", "dictionary"])
def test_custom_charger_cost_survives_complete_run(legacy_model, source):
    parameters = copy.deepcopy(DEFAULTS)
    if source == "dictionary":
        parameters["kick-scooter-charger-2025"]["amount"] = 123.45
        parameters["kick-scooter-charger-2025"]["loc"] = 123.45
        parameters["kick-scooter-charger-2025"]["uncertainty_type"] = 1
        del parameters["kick-scooter-charger-2025"]["minimum"]
        del parameters["kick-scooter-charger-2025"]["maximum"]
    before = copy.deepcopy(parameters)
    model = complete(parameters, array_override=source == "array")
    assert parameters == before
    assert model[PARAMETER].sel(size="Kick-scooter", year=2025).item() == pytest.approx(
        123.45
    )
    assert (model[PARAMETER].sel(size="Kick-scooter", year=[2020, 2030]) == 70).all()
    check_cost_change(legacy_model, model)
