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
installation or network access. Inventory export has optional dependencies:

```bash
python -m pip install "carculator_two_wheeler[excel,brightway]==0.1.1"
```

The Brightway extra supports the legacy stack (`bw2io<0.9`, `bw2data<4`,
`bw2calc<2`). Export currently targets ecoinvent 3.9 and 3.10; importing those
inventories requires the corresponding background database in the destination tool.

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

## Modelling and validation

The vehicle models include native **2025** parameters and documented temporal
extensions. These combine engineering priors and selected calibration evidence;
they are not independent measurements for every vehicle configuration.

`TtW energy` is in kJ/km. For BEVs it is net stored-energy depletion;
`model.battery_terminal_energy` reports terminal DC separately, while
`electricity consumption` is grid electricity in kWh/km. Identify the measurement
boundary before comparing energy outputs. Availability-masked zeroes do not
represent physically zero consumption.

Supported background scenarios are `SSP2-NPi`, `SSP2-PkBudg1000`,
`SSP2-PkBudg650`, and `static`. ReCiPe supports midpoint/endpoint and EF midpoint.
Use fresh model instances for independent cases. `inputs.stochastic(n, seed=...)`
seeds parameter sampling, not every downstream cost adjustment.

See [validation and limitations](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/docs/validity.rst), [migration notes](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/docs/release.rst)
and the [documentation](https://carculator-two-wheeler.readthedocs.io/en/latest/).

The electric-bicycle cost model retains a known negative-cost case, documented by a strict expected-failure test. See the [changelog](https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/blob/main/CHANGELOG.md).

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
