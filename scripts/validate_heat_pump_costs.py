"""Check the heat-pump default correction on all available BEV two-wheeler sizes.

Run: python scripts/validate_heat_pump_costs.py --output /tmp/heat-pump-costs.json
Uses packaged inputs and offline inventories; no Brightway project is needed.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import xarray as xr

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
PARAMETERS = [
    "heat pump cost",
    "purchase cost",
    "amortised purchase cost",
    "total cost per km",
    "glider cost",
    "maintenance cost",
    "energy cost",
    "amortised component replacement cost",
    "driving mass",
    "TtW energy",
]
CHANGED = [
    "heat pump cost",
    "purchase cost",
    "amortised purchase cost",
    "total cost per km",
]


def complete(defaults, sizes, years):
    inputs = TwoWheelerInputParameters(parameters=defaults)
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": sizes, "powertrain": ["BEV"], "year": years}
    )
    model = TwoWheelerModel(array)
    model.set_all()
    inventory = InventoryTwoWheeler(model, functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all()
    matrix_signature = (
        inventory.A.shape,
        str(inventory.A.dtype),
        hashlib.sha256(np.ascontiguousarray(inventory.A).tobytes()).hexdigest(),
    )
    rows = [
        {
            "size": size,
            "powertrain": "BEV",
            "year": year,
            **{p: model[p].sel(size=size, year=year).item() for p in PARAMETERS},
        }
        for size in sizes
        for year in years
    ]
    return model, rows, matrix_signature, impacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; existing reports are not overwritten.")
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    provenance = json.loads((DATA / "heat_pump_cost_provenance.json").read_text())
    previous = {**defaults, **provenance["original_records"]}
    sizes = [s for s in provenance["scope"]["sizes"] if s != "Moped <4kW"]
    years = [2020, 2025, 2030]
    old, before, old_matrix, old_impacts = complete(previous, sizes, years)
    new, after, new_matrix, new_impacts = complete(defaults, sizes, years)
    xr.testing.assert_identical(
        old.array.drop_sel(parameter=CHANGED), new.array.drop_sel(parameter=CHANGED)
    )
    assert old_matrix == new_matrix
    xr.testing.assert_identical(old_impacts, new_impacts)
    np.testing.assert_allclose(
        old["purchase cost"] - new["purchase cost"], 300, rtol=0, atol=0.002
    )
    assert (new["heat pump cost"] == 0).all()
    assert np.isfinite(new["purchase cost"]).all()
    assert (new["purchase cost"] > 0).all()
    assert (new["TtW energy"] > 0).all()
    report = dict(
        schema_version=1,
        review_date="2026-10-08",
        defaults_sha256=hashlib.sha256(
            (DATA / "default_parameters.json").read_bytes()
        ).hexdigest(),
        qualification="Default equipment-scope correction; not empirical ownership-cost calibration. Explicit monetary overrides do not add heat-pump physics or inventory exchanges.",
        units={
            "purchase_and_components": "EUR; legacy price bases retained",
            "per_km_costs": "EUR/vkm",
            "driving mass": "kg",
            "TtW energy": "kJ/km",
        },
        checks={
            "completed_model_inventory_lcia_cases": len(before) + len(after),
            "active_bev_sizes": len(sizes),
            "years": years,
            "all_other_model_parameters_unchanged": True,
            "inventory_matrices_and_lcia_unchanged": True,
            "static_purchase_reduction_EUR": 300,
        },
        before=before,
        after=after,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
