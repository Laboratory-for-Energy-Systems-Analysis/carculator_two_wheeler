"""Small-vehicle cost priors, cash flows and independent component responses."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from carculator_two_wheeler import TwoWheelerInputParameters, TwoWheelerModel
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
PROVENANCE = json.loads((DATA / "small_vehicle_cost_provenance.json").read_text())
CASES = PROVENANCE["cases"]


def test_scoped_priors_preserve_other_classes_and_relative_uncertainty():
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    for key, original in PROVENANCE["original_records"].items():
        affected = [c for c in CASES if c["powertrain"] in original["powertrain"]]
        assert defaults[key] == {
            **original,
            "sizes": [
                s for s in original["sizes"] if s not in {c["size"] for c in affected}
            ],
        }
        for case in affected:
            matching = [
                r
                for r in defaults.values()
                if r["name"] == original["name"]
                and r["year"] == original["year"]
                and case["size"] in r["sizes"]
                and case["powertrain"] in r["powertrain"]
            ]
            assert len(matching) == 1
            record = matching[0]
            assert record["sizes"] == [case["size"]]
            assert record["powertrain"] == [case["powertrain"]]
            if record["name"] == "glider cost slope":
                assert record["loc"] == record["amount"] == case["slope_EUR_per_kg"]
                reconstructed = (
                    record["amount"]
                    * case["reference_mass_kg"]
                    * case["reference_markup"]
                )
                assert reconstructed + case[
                    "reference_non_glider_total_EUR"
                ] == pytest.approx(case["reference_price_EUR"])
                for bound in ("minimum", "maximum"):
                    assert record[bound] / record["amount"] == pytest.approx(
                        original[bound] / original["amount"]
                    )
                assert record["minimum"] > 0
            else:
                assert record["amount"] == record["loc"] == 0
                assert record["uncertainty_type"] == 1
    for case in CASES:
        # An unsupported heat-pump component must not lower the calibrated glider.
        assert "heat pump cost" not in case["reference_non_glider_components_EUR"]


@pytest.fixture(scope="module", params=["minimum", "amount", "maximum"])
def completed_models(request):
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs,
        scope={
            "size": ["Kick-scooter", "Moped <4kW", "Scooter <4kW"],
            "powertrain": ["BEV", "ICEV-p"],
        },
    )
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    for key in PROVENANCE["added_record_keys"]:
        record = defaults[key]
        if record["name"] == "glider cost slope":
            array.loc[
                dict(
                    parameter=record["name"],
                    size=record["sizes"],
                    powertrain=record["powertrain"],
                    year=record["year"],
                )
            ] = record[request.param]
    # A ten-year case allows an independent sum of discounted annual payments.
    array.loc[dict(parameter="lifetime kilometers")] = 10 * array.sel(
        parameter="kilometers per year"
    )
    model = TwoWheelerModel(array)
    model.set_all()
    return model


def test_completed_costs_are_positive_and_repay_capital(completed_models):
    for case in CASES:
        values = completed_models.array.sel(
            size=case["size"],
            powertrain=case["powertrain"],
            year=[2020, 2025, 2030, 2040, 2050],
        )
        costs = values.sel(
            parameter=[
                "glider cost",
                "purchase cost",
                "maintenance cost",
                "total cost per km",
            ]
        )
        assert np.isfinite(costs).all()
        assert (costs > 0).all()
        for year in (2020, 2025, 2030):

            def value(parameter):
                return values.sel(parameter=parameter, year=year).item()

            annual_km = value("kilometers per year")
            rate = value("interest rate")
            assert value("lifetime kilometers") / annual_km == pytest.approx(10)
            repayment = 1 / sum((1 + rate) ** -t for t in range(1, 11))
            purchase = value("purchase cost")
            replacement = value("energy battery cost") * value(
                "battery lifetime replacements"
            )
            annual_maintenance = value("maintenance cost per glider cost") * value(
                "glider cost"
            )
            assert value("amortised purchase cost") * annual_km == pytest.approx(
                purchase * repayment, rel=2e-6
            )
            assert value("maintenance cost") * annual_km == pytest.approx(
                annual_maintenance, rel=2e-6
            )
            expected = (
                (purchase + replacement / (1 + rate) ** 5) * repayment
                + annual_maintenance
            ) / annual_km + value("energy cost")
            assert value("total cost per km") == pytest.approx(expected, rel=2e-6)


@pytest.mark.parametrize(
    "unit_cost, quantity, powertrain",
    [
        ("energy battery cost per kWh", "electric energy stored", "BEV"),
        ("electric powertrain cost per kW", "electric power", "BEV"),
        ("combustion powertrain cost per kW", "combustion power", "ICEV-p"),
    ],
)
def test_component_price_changes_are_not_absorbed_by_glider(
    completed_models, unit_cost, quantity, powertrain
):
    # Reprice a completed vehicle; the calibration residual is frozen input data.
    model = copy.deepcopy(completed_models)
    before = model.array.copy(deep=True)
    model[unit_cost] += 10
    model.set_costs()
    for case in CASES:
        if case["powertrain"] != powertrain:
            continue
        selection = dict(size=case["size"], powertrain=powertrain, year=2025)
        old = before.sel(**selection)
        new = model.array.sel(**selection)
        expected = 10 * old.sel(parameter=quantity) * old.sel(parameter="markup factor")
        assert new.sel(parameter="purchase cost").item() - old.sel(
            parameter="purchase cost"
        ).item() == pytest.approx(expected.item(), rel=1e-4)
        assert (
            new.sel(parameter="glider cost").item()
            == old.sel(parameter="glider cost").item()
        )
