"""Explicit battery prices must reach completed vehicle costs."""

import numpy as np
from carculator_two_wheeler import (
    TwoWheelerInputParameters,
    TwoWheelerModel,
    fill_xarray_from_input_parameters,
)


def test_explicit_battery_price_survives_cost_adjustment():
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs,
        scope={"size": ["Motorcycle 11-35kW"], "powertrain": ["BEV"], "year": [2025]},
    )
    models = []
    for price in (0, 500):
        model = TwoWheelerModel(
            array,
            battery_costs={
                "energy battery cost per kWh": {
                    ("BEV", "Motorcycle 11-35kW", 2025): price
                }
            },
        )
        model.set_all()
        np.testing.assert_allclose(model["energy battery cost per kWh"], price)
        models.append(model)
    low, high = models
    delta = low["electric energy stored"] * 500 * low["markup factor"]
    np.testing.assert_allclose(
        high["purchase cost"] - low["purchase cost"], delta, rtol=2e-6, atol=0.01
    )
    np.testing.assert_allclose(
        high["component replacement cost"] - low["component replacement cost"],
        delta * low["battery lifetime replacements"],
        rtol=2e-6,
        atol=0.01,
    )
    np.testing.assert_array_equal(high["TtW energy"], low["TtW energy"])
