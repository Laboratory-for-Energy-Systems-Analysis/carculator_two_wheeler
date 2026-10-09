# carculator_two_wheeler

Prospective environmental and economic life cycle assessment of bicycles, scooters, mopeds and motorcycles.

[![Installed artifacts](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/actions/workflows/main.yml)
[![PyPI](https://img.shields.io/pypi/v/carculator_two_wheeler)](https://pypi.org/project/carculator_two_wheeler/)

Developed at the [Paul Scherrer Institute](https://www.psi.ch/en).
This checkout prepares **0.1.1**; see [CHANGELOG.md](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/CHANGELOG.md) for release status and changes.

## Installation

Use **Python 3.12** (`>=3.12,<3.13`) and a fresh environment. The shared runtime
requires NumPy `>=1.26.4,<2`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate`. After publication, install
this release from PyPI:

```bash
python -m pip install "carculator_two_wheeler==0.1.1"
```

Before publication, use the matching source checkouts as described under development.
Core calculations use bundled resources and need no Brightway project, ecoinvent
installation or network access. The matching `carculator_utils` runtime installs
`brightpath>=1.0.0a6,<1.1` for Brightway Excel, SimaPro CSV and openLCA JSON-LD
exports. It uses Brightpath's v1 API, currently an alpha; model and LCIA
calculations do not import Brightpath or Brightway.

The `excel` extra remains a compatibility alias. To select the tested legacy
Brightway stack (`bw2io<0.9`, `bw2data<4`, `bw2calc<2`), use:

```bash
python -m pip install "carculator_two_wheeler[brightway]==0.1.1"
```

Brightpath also installs `bw2io` without that extra. Export targets ecoinvent
3.12 cut-off by default; legacy 3.9/3.10 targets reject suppliers without
verified older links. External suppliers must be matched to the corresponding
background in the destination tool. See [inventory export](docs/inventory_export.rst).

## Quick start

```python
from carculator_two_wheeler import (
    TwoWheelerInputParameters,
    TwoWheelerModel,
    InventoryTwoWheeler,
    fill_xarray_from_input_parameters,
)

inputs = TwoWheelerInputParameters()
inputs.static()
_, array = fill_xarray_from_input_parameters(
    inputs,
    scope={
        "size": ["Motorcycle 11-35kW"],
        "powertrain": ["ICEV-p", "BEV"],
        "year": [2025],
    },
)
model = TwoWheelerModel(array)
model.set_all()
print(model["TtW energy"])  # kJ per vehicle-kilometre

inventory = InventoryTwoWheeler(model, functional_unit="vkm")
impacts = inventory.calculate_impacts()
print(impacts.sel(impact_category="climate change").sum("impact"))
```

The example reports impacts per vehicle-kilometre. The petrol motorcycle now
returns about **1.797 MJ/km (5.646 L/100 km)** after restoring the historical
engine-efficiency prior. This fixes the former 1% efficiency defect; the prior
remains provisional, with substantial differences from unmatched manufacturer
consumption figures. See [the correction and sources](docs/petrol_efficiency.rst).
Release 0.1.1 remains unpublished pending review of the remaining known issues.

## Inventory export

With the completed `inventory` from the quick start:

```python
workbook = inventory.export_lci(software="brightway2", format="file", directory="exports")
simapro_csv = inventory.export_lci(software="simapro", format="file", directory="exports")
foreground_zip = inventory.export_lci(software="openlca", format="file", directory="exports")
```

Retain exactly one sample before constructing the model and inventory. Each year
gets its own export; multiple years return a list. Exports preserve the original
inventory and calculated impacts. The default `export_lci()` returns an unlinked
Brightway importer.

The openLCA ZIP contains foreground processes, without an ecoinvent background or
LCIA methods; map external providers and elementary flows before calculation.
SimaPro CSV uses Latin-1 and warns when omitting custom noise flows. See the
[export guide](docs/inventory_export.rst) for return types, sample selection and
format-specific limitations.

## Modelling and validation

Battery unit prices supplied by users now survive chemistry selection and cost
adjustment. Use `battery_costs` for explicit prices scoped by vehicle, year and
sample; see [battery-cost inputs](docs/usage.rst#battery-unit-costs).

The vehicle models include native **2025** parameters and documented temporal
extensions. These combine engineering priors and selected calibration evidence;
they are not independent measurements for every vehicle configuration.

`TtW energy` is in kJ/km. For BEVs it is net stored-energy depletion;
`model.battery_terminal_energy` reports terminal DC separately, while
`electricity consumption` is grid electricity in kWh/km. Identify the measurement
boundary before comparing energy outputs. Availability-masked zeroes do not
represent physically zero consumption.

BEV range targets now converge battery capacity, vehicle mass and cycle energy
together. Fixed-capacity and pack-mass scenarios also propagate through range,
consumption and inventories; see [battery sizing and override examples](docs/bev_sizing.rst).

Two-wheelers no longer force a replacement battery: replacement fractions follow
lifetime energy throughput and can be zero. Initial battery supply is retained;
see [replacement accounting and limits](docs/battery_replacements.rst).

Supported background scenarios are `SSP2-NPi`, `SSP2-PkBudg1000`,
`SSP2-PkBudg650`, and `static`. ReCiPe supports midpoint/endpoint and EF midpoint.
Use fresh model instances for independent cases. `inputs.stochastic(n, seed=...)`
seeds parameter sampling, not every downstream cost adjustment.

See [validation and limitations](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/docs/validity.rst), [migration notes](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/docs/release.rst)
and the [documentation](https://carculator-two-wheeler.readthedocs.io/en/latest/).

Electric-bicycle glider and maintenance costs now use a positive mechanical-bicycle
prior supported by published market data. Complete e-bike prices remain
uncalibrated. Kick-scooter, moped and small-scooter negative glider costs now
use source-based provisional priors as well. The inherited BEV cabin heat-pump
charge is now zero by default; explicit cost overrides remain supported. The
electric kick-scooter charger uses a provisional EUR 70 retail-price proxy;
charger assumptions for other classes still need review. See the
[bicycle correction](docs/bicycle_costs.rst), [small-vehicle costs](docs/small_vehicle_costs.rst),
[heat-pump correction](docs/heat_pump_costs.rst) and
[kick-scooter charger evidence](docs/kick_scooter_charger_costs.rst).

## Development and release

Use matching sibling checkouts, especially `carculator_utils` **1.3.6 or newer**:

```bash
python -m pip install -e "../carculator_utils[test,excel,brightway]" -e ".[test,docs,excel,brightway]"
python -m pip check
python -m pytest
python -m sphinx -b html docs docs/_build/html
```

The `docs` extra includes the extensions used by this repository.
See [RELEASING.md](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/RELEASING.md) for artifact verification, release order and publication.

## Support and license

Contact [carculator@psi.ch](mailto:carculator@psi.ch) or open an [issue](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/issues).
Maintained by [Romain Sacchi](https://github.com/romainsacchi), with contributions
from the carculator development team. See [contributing](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/CONTRIBUTING.md).
Licensed under [BSD-3-Clause](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/LICENSE).

Scientific background: [Cox et al. (2018)](https://doi.org/10.1016/j.apenergy.2017.12.100).

The shared LCA background now uses premise 2.5.4 and ecoinvent 3.12 cutoff.
The former `NMC-523` option is replaced by `NMC-532` (actual Ni:Mn:Co 5:3:2
inventory); update custom chemistry selections. See `docs/release.rst`.
