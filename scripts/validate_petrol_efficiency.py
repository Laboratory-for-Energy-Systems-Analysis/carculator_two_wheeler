"""Reproduce the petrol-default correction and manufacturer screening comparisons.

Run with matching installed/source packages (no network or Brightway project):
    python scripts/validate_petrol_efficiency.py --output /tmp/petrol-audit.json

Manufacturer observations are not matched-cycle validation targets. The audit
uses default masses, road loads, fuel blends and the bundled Two wheeler cycle.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from carculator_utils.background_systems import BackgroundSystemModel

from carculator_two_wheeler import (
    InventoryTwoWheeler,
    TwoWheelerInputParameters,
    TwoWheelerModel,
)
from carculator_two_wheeler import __file__ as package_file
from carculator_two_wheeler import fill_xarray_from_input_parameters

DATA = Path(package_file).parent / "data"
SIZES = [
    "Moped <4kW",
    "Scooter <4kW",
    "Scooter 4-11kW",
    "Motorcycle 4-11kW",
    "Motorcycle 11-35kW",
]
YEARS = [2020, 2025, 2030]


def run_case(original_records=None, years=YEARS, inventory_checks=True):
    """Complete a model and optionally check actual supplier and carbon exchanges."""
    inputs = TwoWheelerInputParameters()
    inputs.static()
    _, array = fill_xarray_from_input_parameters(
        inputs, scope={"size": SIZES, "powertrain": ["ICEV-p"]}
    )
    if original_records:
        for record in original_records.values():
            if record["year"] in array.year:
                array.loc[
                    dict(
                        size=record["sizes"],
                        parameter="engine efficiency",
                        year=record["year"],
                    )
                ] = record["amount"]
    array = array.interp(year=years)
    model = TwoWheelerModel(array)
    model.set_all()
    records = []
    for size in SIZES:
        for year in years:
            row = {"size": size, "year": year}
            for parameter, key, multiplier in (
                ("engine efficiency", "engine_efficiency", 1),
                ("TtW energy", "fuel_energy_kJ_per_km", 1),
                ("fuel consumption", "fuel_L_per_100km", 100),
                ("driving mass", "driving_mass_kg", 1),
            ):
                row[key] = (
                    model[parameter].sel(size=size, year=year).item() * multiplier
                )
            records.append(row)
    if not inventory_checks:
        return records

    inventory = InventoryTwoWheeler(model, functional_unit="vkm")
    impacts = inventory.calculate_impacts()
    assert np.isfinite(impacts).all(), "Nonfinite LCIA result"
    specs = BackgroundSystemModel().fuel_specs
    blend = model.fuel_blend["petrol"]
    lhv = sum(c["share"] * specs[c["type"]]["lhv"] for c in blend.values())
    (market,) = inventory.find_input_indices(("fuel supply for petrol vehicles",))
    for component in blend.values():
        supplier = inventory.inputs[tuple(specs[component["type"]]["name"])]
        np.testing.assert_allclose(
            -inventory.A[:, supplier, market, :],
            np.asarray(component["share"])[None, :],
            atol=1e-8,
        )
    for size in SIZES:
        (column,) = inventory.find_input_indices(
            (f"transport, {model.vehicle_type}, ", ", ICEV-p,", size)
        )
        mass = model["TtW energy"].sel(size=size, powertrain="ICEV-p").values[:, 0] / (
            lhv * 1000
        )
        purchased = -inventory.A[0, market, column, :]
        np.testing.assert_allclose(purchased, mass, rtol=2e-5)
        exchanges = {"fuel_supply_kg_per_km": purchased}
        for biogenic, label in ((False, "fossil"), (True, "non-fossil")):
            carbon = sum(
                c["share"]
                * specs[c["type"]]["co2"]
                * (
                    specs[c["type"]]["biogenic_share"]
                    if biogenic
                    else 1 - specs[c["type"]]["biogenic_share"]
                )
                for c in blend.values()
            )
            flow = inventory.inputs[(f"Carbon dioxide, {label}", ("air",), "kilogram")]
            actual = -inventory.A[0, flow, column, :]
            np.testing.assert_allclose(actual, mass * carbon, rtol=2e-5, atol=1e-9)
            exchanges[f"co2_{label}_kg_per_km"] = actual
        for row in (r for r in records if r["size"] == size):
            index = years.index(row["year"])
            row.update({k: float(v[index]) for k, v in exchanges.items()})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output path; existing reports are not overwritten.")
    provenance = json.loads((DATA / "petrol_efficiency_provenance.json").read_text())
    catalog_path = (
        Path(__file__).resolve().parents[1]
        / "tests/fixtures/petrol_consumption_sources.json"
    )
    catalog = json.loads(catalog_path.read_text())
    before = run_case(provenance["original_records"])
    after = run_case()
    annual = run_case(years=list(range(2015, 2041)), inventory_checks=False)
    comparisons = []
    for observation in catalog["observations"]:
        modeled = next(
            r for r in after if r["size"] == observation["size"] and r["year"] == 2025
        )["fuel_L_per_100km"]
        reported = observation["reported_L_per_100km"]
        comparisons.append(
            {
                "id": observation["id"],
                "model_2025_L_per_100km": modeled,
                "reported_L_per_100km": reported,
                "deviation_percent": 100 * (modeled / reported - 1),
                "classification": "unmatched screening only",
            }
        )
    report = {
        "schema_version": 1,
        "review_date": "2026-10-08",
        "defaults_sha256": hashlib.sha256(
            (DATA / "default_parameters.json").read_bytes()
        ).hexdigest(),
        "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "cycle": "Two wheeler cycle (bundled size-specific traces)",
        "scope": "Five ICEV-p classes; default blend, mass, road load and auxiliaries",
        "qualification": "Provisional prior restoration, not an empirical calibration",
        "checks": {
            "completed_model_inventory_lcia_cases": len(before) + len(after),
            "fuel_supplier_and_tailpipe_carbon_balance": "passed for all cases",
            "annual_model_cases": len(annual),
        },
        "before": before,
        "after": after,
        "annual": annual,
        "manufacturer_screening": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
