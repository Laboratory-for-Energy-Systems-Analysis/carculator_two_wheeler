"""Audit small-vehicle costs on completed models, inventories and annual runs.

Run: python scripts/validate_small_vehicle_costs.py --output /tmp/small-costs.json
No network, Brightway project or ecoinvent installation is required.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml
from carculator_utils import __file__ as utils_file

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
PROVENANCE = json.loads((DATA / "small_vehicle_cost_provenance.json").read_text())
CASES = PROVENANCE["cases"]
PURCHASE = yaml.safe_load(
    (Path(utils_file).parent / "data/purchase_cost_params.yaml").read_text()
)["purchase"]
PARAMETERS = [
    "purchase cost",
    "maintenance cost",
    "amortised purchase cost",
    "amortised component replacement cost",
    "energy cost",
    "total cost per km",
    "glider base mass",
    "glider cost slope",
    "glider cost intercept",
    "driving mass",
    "TtW energy",
]


def complete(defaults, years, with_inventory=False):
    rows, matrices, impacts = [], [], []
    # Separate cases avoid unsupported size/powertrain Cartesian combinations.
    for case in CASES:
        inputs = TwoWheelerInputParameters(parameters=defaults)
        inputs.static()
        _, native = fill_xarray_from_input_parameters(
            inputs, scope={"size": [case["size"]], "powertrain": [case["powertrain"]]}
        )
        model = TwoWheelerModel(native.interp(year=years))
        model.set_all()
        parameters = PARAMETERS + [p for p in PURCHASE if p in model.array.parameter]
        rows.extend(
            {
                "size": case["size"],
                "powertrain": case["powertrain"],
                "year": year,
                **{p: model[p].sel(year=year).item() for p in parameters},
            }
            for year in years
        )
        if with_inventory:
            inventory = InventoryTwoWheeler(model, functional_unit="vkm")
            result = inventory.calculate_impacts()
            assert np.isfinite(result).all()
            impacts.append(result)
            matrices.append(
                (
                    inventory.A.shape,
                    str(inventory.A.dtype),
                    hashlib.sha256(
                        np.ascontiguousarray(inventory.A).tobytes()
                    ).hexdigest(),
                )
            )
    return rows, matrices, impacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; existing reports are not overwritten.")
    current = json.loads((DATA / "default_parameters.json").read_text())
    original = {
        k: v for k, v in current.items() if k not in PROVENANCE["added_record_keys"]
    }
    original.update(PROVENANCE["original_records"])
    before, old_matrices, old_impacts = complete(original, [2020, 2025, 2030], True)
    after, matrices, impacts = complete(current, [2020, 2025, 2030], True)
    for old, new in zip(old_matrices, matrices):
        assert new == old
    for old, new in zip(old_impacts, impacts):
        np.testing.assert_array_equal(new, old)
    for old, new in zip(before, after):
        for parameter in ("driving mass", "TtW energy"):
            assert old[parameter] == new[parameter]
        for parameter in (
            "glider cost",
            "purchase cost",
            "maintenance cost",
            "total cost per km",
        ):
            assert np.isfinite(new[parameter]) and new[parameter] > 0
    annual, _, _ = complete(current, list(range(2015, 2041)))
    trends = []
    for case in CASES:
        rows = [
            r
            for r in annual
            if (r["size"], r["powertrain"]) == (case["size"], case["powertrain"])
        ]
        assert all(
            r["total cost per km"] > 0 and r["glider cost intercept"] == 0 for r in rows
        )
        slopes = [r["glider cost slope"] for r in rows]
        np.testing.assert_allclose(slopes, slopes[0], rtol=1e-7)
        trends.append(
            {
                "size": case["size"],
                "powertrain": case["powertrain"],
                "maximum_absolute_annual_purchase_change_percent": 100
                * max(
                    abs(b["purchase cost"] / a["purchase cost"] - 1)
                    for a, b in zip(rows, rows[1:])
                ),
            }
        )
    report = {
        "schema_version": 1,
        "review_date": "2026-10-08",
        "defaults_sha256": hashlib.sha256(
            (DATA / "default_parameters.json").read_bytes()
        ).hexdigest(),
        "qualification": "Provisional cost priors; residual calibration is not independent validation. See the reported component breakdown and current cost documentation for remaining limitations.",
        "units": {
            "purchase_components": "EUR; source dates and boundaries in packaged provenance, legacy components have mixed price bases",
            "per_km_costs": "EUR/vkm",
            "TtW energy": "kJ/km",
            "driving mass": "kg",
        },
        "checks": {
            "completed_model_inventory_lcia_cases": len(before) + len(after),
            "unchanged_mass_energy_inventory_and_lcia": True,
            "annual_model_cases": len(annual),
            "constant_glider_coefficients_across_years": True,
        },
        "before": before,
        "after": after,
        "annual": annual,
        "trends": trends,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
