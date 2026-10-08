"""Bicycle cost priors and independent cash-flow checks on completed models."""

import json
from pathlib import Path

import numpy as np
import pytest

from carculator_two_wheeler import (
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
SIZES = ["Bicycle <25", "Bicycle <45", "Bicycle cargo"]


def test_bicycle_prior_has_disjoint_scope_and_preserves_relative_uncertainty():
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    provenance = json.loads((DATA / "bicycle_cost_provenance.json").read_text())
    for key, original in provenance["original_records"].items():
        remainder = defaults[key]
        assert remainder == {
            **original,
            "sizes": [s for s in original["sizes"] if s not in SIZES],
        }
        matching = [
            r
            for r in defaults.values()
            if r["name"] == original["name"]
            and r["year"] == original["year"]
            and "BEV" in r["powertrain"]
            and set(r["sizes"]) & set(SIZES)
        ]
        assert len(matching) == 1
        record = matching[0]
        assert record["sizes"] == SIZES
        assert record["powertrain"] == ["BEV"]
        if record["name"] == "glider cost slope":
            # The source price already includes retail markup: account for it once.
            assert record["amount"] * 12 * 1.2 == pytest.approx(500)
            for bound in ("minimum", "maximum"):
                assert record[bound] / record["amount"] == pytest.approx(
                    original[bound] / original["amount"]
                )
            assert record["minimum"] > 0
        else:
            assert record["amount"] == record["loc"] == 0
            assert record["uncertainty_type"] == 1


@pytest.fixture(scope="module", params=["minimum", "amount", "maximum"])
def completed_bicycles(request):
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": SIZES, "powertrain": ["BEV"]}
    )
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    for record in defaults.values():
        if record["name"] == "glider cost slope" and record["sizes"] == SIZES:
            array.loc[dict(parameter="glider cost slope", year=record["year"])] = (
                record[request.param]
            )
    model = TwoWheelerModel(array)
    model.set_all()
    return model


def test_completed_bicycle_costs_are_positive_at_uncertainty_endpoints(
    completed_bicycles,
):
    model = completed_bicycles
    for parameter in (
        "glider cost",
        "purchase cost",
        "maintenance cost",
        "total cost per km",
    ):
        values = model[parameter].sel(year=[2020, 2025, 2030, 2040, 2050])
        assert np.isfinite(values).all(), parameter
        assert (values > 0).all(), parameter


def test_completed_bicycle_costs_repay_capital_and_balance_maintenance(
    completed_bicycles,
):
    model = completed_bicycles
    for size in SIZES:
        for year in (2020, 2025, 2030):

            def value(parameter):
                return model[parameter].sel(size=size, year=year).item()

            annual_km = value("kilometers per year")
            years = value("lifetime kilometers") / annual_km
            assert years == pytest.approx(10)
            rate = value("interest rate")
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
            expected_total = (
                (purchase + replacement / (1 + rate) ** 5) * repayment
                + annual_maintenance
            ) / annual_km + value("energy cost")
            assert value("total cost per km") == pytest.approx(expected_total, rel=2e-6)
