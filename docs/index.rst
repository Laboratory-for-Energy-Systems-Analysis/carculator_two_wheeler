.. image:: /_static/img/mediumsmall_2.png
   :align: center

.. raw:: html

    <p align="center">
      <a href="https://badge.fury.io/py/carculator_two_wheeler" target="_blank"><img src="https://badge.fury.io/py/carculator_two_wheeler.svg"></a>
      <a href="https://github.com/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://github.com/romainsacchi/carculator_two_wheeler/actions/workflows/main.yml/badge.svg?branch=master"></a>
      <a href="https://ci.appveyor.com/project/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://ci.appveyor.com/api/projects/status/github/romainsacchi/carculator_two_wheeler?svg=true"></a>
      <a href="https://coveralls.io/github/romainsacchi/carculator_two_wheeler" target="_blank"><img src="https://coveralls.io/repos/github/romainsacchi/carculator_two_wheeler/badge.svg"></a>
      <a href="https://carculator_two_wheeler.readthedocs.io/en/latest/" target="_blank"><img src="https://readthedocs.org/projects/carculator_two_wheeler/badge/?version=latest"></a>
      <a href="https://doi.org/10.5281/zenodo.3778259"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.3778259.svg" alt="DOI"></a>
    </p>


.. _intro:

Carculator Two-Wheeler
======================

``carculator_two_wheeler`` is a parameterized model that allows to generate and characterize life cycle inventories for different
two-wheeler configurations, according to selected:

* powertrain technologies (9): petrol engine, diesel engine, electric motor, hybrid, plugin-hybrid, etc.,
* year of operation (2): 2000, 2010, 2020, 2040 (with the possibility to interpolate in between, and up to 2050)
* and sizes (7): Mini, Large, etc.

The methodology used to develop ``carculator_two_wheeler`` is explained in an article :cite:`ct-1131`.

At the moment, the tool has a focus on two-wheeler vehicles.

It was initially based on the model developed in :cite:`ct-1132`.

More specifically, ``carculator_two_wheeler`` generates `Brightway2 <https://brightway.dev/>`_ and
`SimaPro <https://www.simapro.com/>`_ compatible inventories, but also directly provides characterized results against several midpoint indicators from the impact assessment method *ReCiPe* as well as life cycle cost indicators.

``carculator_two_wheeler`` is a special in the way that it uses time- and energy-scenario-differentiated background inventories for the future,
resulting from the coupling between the `ecoinvent 3.6 database <https://ecoinvent.org>`_ and the scenario outputs of PIK's
integrated assessment model `REMIND <https://www.pik-potsdam.de/research/transformation-pathways/models/remind/remind>`_.
This allows to perform prospective study while consider future expected changes in regard to the production of electricity,
cement, steel, heat, etc.

Objective
---------

The objective is to produce life cycle inventories for two-wheeler vehicles in a transparent, comprehensive and quick manner,
to be further used in prospective LCA of transportation technologies.

Why?
----

Many life cycle assessment (LCA) models of passenger cars exist. Yet, because LCA of vehicles, particularly for electric battery vehicles,
are sensitive to assumptions made in regards to electricity mix used for charging, lifetime of the battery, etc., it has led
to mixed conclusions being published in the scientific literature. Because the underlying calculations are kept undocumented,
it is not always possible to explain the disparity in the results given by these models, which can contribute to adding confusion among the public.

Because ``carculator_two_wheeler`` is kept **as open as possible**, the methods and assumptions behind the generation of results are
easily identifiable and adjustable.
Also, there is an effort to keep the different modules (classes) separated, so that improving certain areas of the model is relatively
easy and does not require changing extensive parts of the code. In that regard, contributions are welcome.

Finally, beside being more flexible and transparent, ``carculator_two_wheeler`` provides interesting features, such as:

* a stochastic mode, that allows fast Monte Carlo analyses, to include uncertainty at the vehicle level
* possibility to override any or all of the 200+ default input vehicle parameters (e.g., load factor, drag coefficient) but also calculated parameters (e.g., driving mass).
* hot pollutants emissions as a function of the driving cycle, using `HBEFA <https://www.hbefa.net/e/index.html>`_ 4.1 data, further divided between rural, suburban and urban areas
* noise emissions, based on `CNOSSOS-EU <https://ec.europa.eu/jrc/en/publication/reference-reports/common-noise-assessment-methods-europe-cnossos-eu>`_ models for noise emissions and an article by :cite:`ct-1015` for inventory modelling and mid- and endpoint characterization of noise emissions, function of driving cycle and further divided between rural, suburban and urban areas
* export of inventories as an Excel/CSV file, to be used with Brightway2 or Simapro, including uncertainty information. This requires the user to have `ecoinvent` installed on the LCA software the bus inventories are exported to.
* export inventories directly into Brightway2, as a LCIImporter object to be registered. Additionally, when run in stochastic mode, it is possible to export arrays of pre-sampled values using the `presamples <https://pypi.org/project/presamples/>`_ library to be used together with the Monte Carlo function of Brightway2.
* development of an online graphical user interface: `carculator online <https://carculator.psi.ch/start>`_

Get started with :ref:`Installation <install>` and continue with an overview about :ref:`how to use the library <usage>`.

User's Guide
------------

.. toctree::
   :maxdepth: 2

   installation
   usage
   modeling
   structure
   validity

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api

.. toctree::
   :maxdepth: 2
   :hidden:

   references/references
   annexes
