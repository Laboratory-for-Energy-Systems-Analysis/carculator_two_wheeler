"""Human bicycle ownership costs must include purchase and maintenance once."""

import numpy as np
import pytest
from carculator_two_wheeler import (
    TwoWheelerInputParameters,
    TwoWheelerModel,
    InventoryTwoWheeler,
    fill_xarray_from_input_parameters,
)


def test_human_bicycle_costs_match_discounted_cash_flows_across_years():
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs,
        scope={
            "size": ["Bicycle <25"],
            "powertrain": ["Human"],
            "year": [2020, 2025, 2030],
        },
    )
    model = TwoWheelerModel(array)
    model.set_all()
    assert np.isfinite(
        InventoryTwoWheeler(model, scenario="static").calculate_impacts()
    ).all()
    np.testing.assert_allclose(model["purchase cost"], 500, rtol=1e-6)
    np.testing.assert_allclose(
        model["maintenance cost"] * model["kilometers per year"], 12.5, rtol=1e-6
    )
    for year in model.array.year.values:
        cell = model.array.sel(year=year)
        rate = cell.sel(parameter="interest rate").item()
        km = cell.sel(parameter="kilometers per year").item()
        years = int(round(cell.sel(parameter="lifetime kilometers").item() / km))
        annuity = 500 / sum((1 + rate) ** -n for n in range(1, years + 1))
        assert cell.sel(parameter="total cost per km").item() == pytest.approx(
            (annuity + 12.5) / km, rel=1e-6
        )
