from copy import deepcopy

import numpy as np
import pytest
from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
    fill_xarray_from_input_parameters,
)


@pytest.fixture(scope="module")
def _model():
    ip = TwoWheelerInputParameters()
    ip.static()
    _, array = fill_xarray_from_input_parameters(
        ip, scope={"size": ["Bicycle <25", "Motorcycle 11-35kW"], "year": [2020]}
    )
    model = TwoWheelerModel(array)
    model.set_all()
    return model


@pytest.fixture
def model(_model):
    return deepcopy(_model)


def test_model_results(model):
    for parameter in ["curb mass", "TtW energy"]:
        assert np.all(np.isfinite(model[parameter])), parameter
        assert np.all(model[parameter] >= 0), parameter
    battery = model.array.sel(powertrain="BEV", size="Bicycle <25")
    assert battery.sel(parameter="battery cell energy density").item() > 0
    np.testing.assert_allclose(
        battery.sel(parameter="electric energy stored"),
        battery.sel(parameter="battery cell mass")
        * battery.sel(parameter="battery cell energy density"),
        rtol=1e-5,
    )


def test_lcia(model):
    results = InventoryTwoWheeler(model).calculate_impacts()
    assert np.all(np.isfinite(results))
    assert "climate change" in results.impact_category


@pytest.mark.xfail(
    strict=True,
    reason="Known data/cost defect: electric bicycle glider cost is negative; requires scientific review",
)
def test_electric_bicycle_cost_is_nonnegative(model):
    assert (
        model.array.sel(
            size="Bicycle <25", powertrain="BEV", parameter="total cost per km"
        ).item()
        >= 0
    )
