"""Audit the bicycle cost correction on completed models and LCIA results.

Run with matching checkouts installed:
    python scripts/validate_bicycle_costs.py --output /tmp/bicycle-costs.json

No downloads, Brightway project or ecoinvent installation are required.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
SIZES = ["Bicycle <25", "Bicycle <45", "Bicycle cargo"]
PARAMETERS = [
    "glider cost",
    "purchase cost",
    "maintenance cost",
    "amortised purchase cost",
    "amortised component replacement cost",
    "energy cost",
    "total cost per km",
    "glider base mass",
    "driving mass",
    "TtW energy",
]


def complete(defaults, years, with_inventory=False):
    inputs = TwoWheelerInputParameters(parameters=defaults)
    inputs.static()
    _, native = fill_xarray_from_input_parameters(
        inputs, scope={"size": SIZES, "powertrain": ["BEV"]}
    )
    model = TwoWheelerModel(native.interp(year=years))
    model.set_all()
    rows = [
        {
            "size": size,
            "year": year,
            **{
                parameter: model[parameter].sel(size=size, year=year).item()
                for parameter in PARAMETERS
            },
        }
        for size in SIZES
        for year in years
    ]
    impacts = None
    if with_inventory:
        impacts = InventoryTwoWheeler(model, functional_unit="vkm").calculate_impacts()
        assert np.isfinite(impacts).all()
    return rows, impacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; existing reports are not overwritten.")
    current = json.loads((DATA / "default_parameters.json").read_text())
    provenance = json.loads((DATA / "bicycle_cost_provenance.json").read_text())
    original = {
        k: v for k, v in current.items() if k not in provenance["added_record_keys"]
    }
    original.update(provenance["original_records"])
    before, baseline_impacts = complete(
        original, [2020, 2025, 2030], with_inventory=True
    )
    after, impacts = complete(current, [2020, 2025, 2030], with_inventory=True)
    np.testing.assert_allclose(impacts, baseline_impacts, rtol=1e-7, atol=1e-12)
    for old, new in zip(before, after):
        for physical in ("driving mass", "TtW energy"):
            assert old[physical] == new[physical]
        for cost in (
            "glider cost",
            "purchase cost",
            "maintenance cost",
            "total cost per km",
        ):
            assert new[cost] > 0
    annual, _ = complete(current, list(range(2015, 2041)))
    trends = []
    for size in SIZES:
        rows = [r for r in annual if r["size"] == size]
        assert all(r["total cost per km"] > 0 for r in rows)
        trends.append(
            {
                "size": size,
                "maximum_absolute_annual_purchase_change_percent": 100
                * max(
                    abs(b["purchase cost"] / a["purchase cost"] - 1)
                    for a, b in zip(rows, rows[1:])
                ),
            }
        )
    ebike_2025 = next(
        r for r in after if r["size"] == "Bicycle <25" and r["year"] == 2025
    )
    report = {
        "schema_version": 1,
        "review_date": "2026-10-08",
        "defaults_sha256": hashlib.sha256(
            (DATA / "default_parameters.json").read_bytes()
        ).hexdigest(),
        "qualification": "Mechanical-bicycle cost proxy; not a complete e-bike market calibration",
        "units": {
            "glider cost": "EUR, new component in constant 2025 EUR",
            "purchase cost": "EUR, other components retain legacy price bases",
            "per_km_costs": "EUR/vkm",
        },
        "checks": {
            "completed_model_inventory_lcia_cases": len(before) + len(after),
            "unchanged_mass_energy_and_lcia": True,
            "annual_model_cases": len(annual),
        },
        "before": before,
        "after": after,
        "annual": annual,
        "trends": trends,
        "market_screening": {
            "reported_2025_e_bike_mean_EUR": 2550,
            "model_2025_EUR": ebike_2025["purchase cost"],
            "deviation_percent": 100 * (ebike_2025["purchase cost"] / 2550 - 1),
            "source": provenance["source"]["url"],
            "qualification": "German all-channel market average; vehicle mix and cost boundaries not matched",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
