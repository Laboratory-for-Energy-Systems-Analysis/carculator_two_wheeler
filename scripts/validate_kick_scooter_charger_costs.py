"""Audit the kick-scooter charger prior on completed models and offline LCIA.

Run: python scripts/validate_kick_scooter_charger_costs.py --output /tmp/charger.json
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
PARAMETER = "battery onboard charging infrastructure cost"
CHANGED = [PARAMETER, "purchase cost", "amortised purchase cost", "total cost per km"]
PARAMETERS = CHANGED + [
    "glider cost",
    "maintenance cost",
    "energy cost",
    "amortised component replacement cost",
    "charger mass",
    "charger efficiency",
    "driving mass",
    "TtW energy",
]
SIZES = ["Kick-scooter", "Bicycle <25", "Scooter <4kW", "Motorcycle >35kW"]


def complete(defaults, sizes, years, previous_records=None, inventory=True):
    inputs = TwoWheelerInputParameters(parameters=defaults)
    inputs.static()
    _, native = fill_xarray_from_input_parameters(
        inputs, scope={"size": sizes, "powertrain": ["BEV"]}
    )
    if previous_records:
        for old in previous_records.values():
            native.loc[
                dict(parameter=PARAMETER, size="Kick-scooter", year=old["year"])
            ] = old["amount"]
    model = TwoWheelerModel(native.interp(year=years))
    model.set_all()
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
    signature, impacts = None, None
    if inventory:
        inv = InventoryTwoWheeler(model, functional_unit="vkm")
        impacts = inv.calculate_impacts()
        assert np.isfinite(impacts).all()
        signature = (
            inv.A.shape,
            str(inv.A.dtype),
            hashlib.sha256(np.ascontiguousarray(inv.A).tobytes()).hexdigest(),
        )
    return model, rows, signature, impacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new output path; existing reports are not overwritten.")
    defaults = json.loads((DATA / "default_parameters.json").read_text())
    provenance = json.loads(
        (DATA / "kick_scooter_charger_cost_provenance.json").read_text()
    )
    old, before, old_matrix, old_impacts = complete(
        defaults, SIZES, [2020, 2025, 2030], provenance["original_records"]
    )
    new, after, new_matrix, new_impacts = complete(defaults, SIZES, [2020, 2025, 2030])
    xr.testing.assert_identical(
        old.array.drop_sel(parameter=CHANGED), new.array.drop_sel(parameter=CHANGED)
    )
    xr.testing.assert_identical(
        old.array.sel(size=SIZES[1:]), new.array.sel(size=SIZES[1:])
    )
    assert old_matrix == new_matrix
    xr.testing.assert_identical(old_impacts, new_impacts)
    np.testing.assert_allclose(
        new["purchase cost"] - old["purchase cost"],
        new[PARAMETER] - old[PARAMETER],
        rtol=1e-6,
        atol=1e-8,
    )
    assert (new["purchase cost"] > 0).all() and (new["total cost per km"] > 0).all()
    _, annual, _, _ = complete(
        defaults, ["Kick-scooter"], list(range(2015, 2041)), inventory=False
    )
    assert all(r[PARAMETER] == 70 and r["total cost per km"] > 0 for r in annual)
    report = dict(
        schema_version=1,
        review_date="2026-10-08",
        defaults_sha256=hashlib.sha256(
            (DATA / "default_parameters.json").read_bytes()
        ).hexdigest(),
        qualification="Provisional charger retail-price proxy; neither OEM cost evidence nor independent validation of complete vehicle price. Earlier glider assumptions remain frozen.",
        units={
            "purchase_and_components": "EUR; mixed source price dates remain",
            "per_km_costs": "EUR/vkm",
            "masses": "kg",
            "TtW energy": "kJ/km",
        },
        checks={
            "completed_model_inventory_lcia_cases": len(before) + len(after),
            "kick_scooter_inventory_cases": 6,
            "control_inventory_cases": 18,
            "unchanged_other_model_parameters": True,
            "unchanged_control_vehicles": True,
            "unchanged_inventory_and_lcia": True,
            "annual_model_cases": len(annual),
            "constant_charger_prior": True,
        },
        before=before,
        after=after,
        annual=annual,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
