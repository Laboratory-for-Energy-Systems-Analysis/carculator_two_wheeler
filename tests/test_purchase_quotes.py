"""Complete retail quotes replace component totals without changing vehicle physics."""

import numpy as np
import pytest
import xarray as xr
from carculator_two_wheeler import (
    TwoWheelerInputParameters,
    TwoWheelerModel,
    InventoryTwoWheeler,
    fill_xarray_from_input_parameters,
)


def inputs():
    parameters = TwoWheelerInputParameters()
    parameters.static()
    _, array = fill_xarray_from_input_parameters(
        parameters,
        scope={
            "size": ["Bicycle <25"],
            "powertrain": ["BEV"],
            "year": [2020, 2025, 2030],
        },
    )
    return array


def test_complete_quote_replaces_components_and_survives_repeat_runs():
    array = inputs()
    base = TwoWheelerModel(array)
    base.set_all()
    quoted = array.copy(deep=True)
    quoted.loc[dict(parameter="purchase cost", year=2025)] = 2550
    quoted.loc[dict(parameter="interest rate")] = 0
    model = TwoWheelerModel(quoted)
    model.set_all()
    assert model["purchase cost"].sel(year=2025).item() == 2550
    for year in [2020, 2030]:
        np.testing.assert_allclose(
            model["purchase cost"].sel(year=year), base["purchase cost"].sel(year=year)
        )
    lifetime = model["lifetime kilometers"].sel(year=2025).item()
    assert model["amortised purchase cost"].sel(year=2025).item() == pytest.approx(
        2550 / lifetime
    )
    before = model.array.copy(deep=True)
    model.set_all()
    xr.testing.assert_allclose(model.array, before)
    for parameter in ["driving mass", "electric energy stored", "TtW energy"]:
        xr.testing.assert_allclose(model[parameter], base[parameter])
    inv = InventoryTwoWheeler(model, scenario="static")
    baseline = InventoryTwoWheeler(base, scenario="static")
    np.testing.assert_array_equal(inv.A, baseline.A)
    xr.testing.assert_allclose(inv.calculate_impacts(), baseline.calculate_impacts())


@pytest.mark.parametrize("quote", [-1, np.nan, np.inf])
def test_invalid_purchase_quote_is_rejected(quote):
    array = inputs()
    array.loc[dict(parameter="purchase cost", year=2025)] = quote
    model = TwoWheelerModel(array)
    with pytest.raises(ValueError, match="Purchase cost"):
        model.set_all()
