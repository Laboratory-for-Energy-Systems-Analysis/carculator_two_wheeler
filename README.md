# ``carculator_two_wheeler``

<p align="center">
  <img style="height:130px;" src="https://github.com/romainsacchi/coarse/raw/master/docs/mediumsmall.png">
</p>

<p align="center">
  <a href="https://badge.fury.io/py/carculator_two_wheeler" target="_blank"><img src="https://badge.fury.io/py/carculator_two_wheeler.svg"></a>
  <a href="https://github.com/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://github.com/romainsacchi/carculator_two_wheeler/actions/workflows/main.yml/badge.svg?branch=master"></a>
  <a href="https://ci.appveyor.com/project/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://ci.appveyor.com/api/projects/status/github/romainsacchi/carculator_two_wheeler?svg=true"></a>
  <a href="https://coveralls.io/github/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://coveralls.io/repos/github/romainsacchi/carculator_two_wheeler/badge.svg"></a>
  <a href="https://carculator_two_wheeler.readthedocs.io/en/latest/" target="_blank"><img src="https://readthedocs.org/projects/carculator_two_wheeler/badge/?version=latest"></a>
  <a href="https://doi.org/10.5281/zenodo.3778259"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.3778259.svg" alt="DOI"></a>
</p>

Prospective life cycle assessment of two-wheelers made blazing fast.

A fully parameterized Python model developed by the [Technology Assessment group](https://www.psi.ch/en/ta) of the
[Paul Scherrer Institut](https://www.psi.ch/en) to perform life cycle assessments (LCA) of two-wheelers.
Builds upon the initial LCA model developed by [Cox et al. 2018](https://doi.org/10.1016/j.apenergy.2017.12.100).

See [the documentation](https://carculator_two_wheeler.readthedocs.io/en/latest/index.html) for more detail, validation, etc.

### Why ``carculator_two_wheeler``?

``carculator_two_wheeler`` allows to:
* produce [life cycle assessment (LCA)](https://en.wikipedia.org/wiki/Life-cycle_assessment) results that include conventional midpoint impact assessment indicators as well cost indicators
*  ``carculator_two_wheeler`` uses time- and energy scenario-differentiated background inventories for the future, based on outputs of Integrated Asessment Model [REMIND](https://www.pik-potsdam.de/research/transformation-pathways/models/remind/remind).
* calculate hot pollutant and noise emissions based on a specified driving cycle
* produce error propagation analyzes (i.e., Monte Carlo) while preserving relations between inputs and outputs
* control all the parameters sensitive to the foreground model (i.e., the vehicles) but also to the background model
(i.e., supply of fuel, battery chemistry, etc.)
* and easily export the vehicle models as inventories to be further imported in the [Brightway2](https://brightwaylca.org/) LCA framework
  or the [SimaPro](https://www.simapro.com/) LCA software.

``carculator_two_wheeler`` integrates well with the [Brightway](https://brightwaylca.org/) LCA framework.

## Install

``carculator_two_wheeler`` is at an early stage of development and is subject to continuous change and improvement.
Three ways of installing ``carculator_two_wheeler`` are suggested.

We recommend the installation on **Python 3.7 or above**.

### Installation of the latest version, using conda

    conda install -c romainsacchi carculator_two_wheeler

### Installation of a stable release (1.3.1) from Pypi

    pip install carculator_two_wheeler

## Usage

### As a Python library



For more examples, see [examples](https://github.com/romainsacchi/carculator_two_wheeler/blob/master/examples/Examples.ipynb).

## As a Web app

``carculator_two_wheeler`` has a [graphical user interface](https://carculator_two_wheeler.psi.ch) for fast comparisons of vehicles.

## Support

Do not hesitate to contact the development team at [carculator_two_wheeler@psi.ch](mailto:carculator_two_wheeler@psi.ch).

## Maintainers

* [Romain Sacchi](https://github.com/romainsacchi)
* [Chris Mutel](https://github.com/cmutel/)

## Contributing

See [contributing](https://github.com/romainsacchi/carculator_two_wheeler/blob/master/CONTRIBUTING.md).

## License

[BSD-3-Clause](https://github.com/romainsacchi/carculator_two_wheeler/blob/master/LICENSE). Copyright 2020 Paul Scherrer Institut.
