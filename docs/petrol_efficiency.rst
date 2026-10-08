Petrol efficiency correction and evidence
=========================================

The 2026-10-08 correction restores the historical engine-efficiency prior for
five petrol classes: ``Moped <4kW``, ``Scooter <4kW``, ``Scooter 4-11kW``,
``Motorcycle 4-11kW`` and ``Motorcycle 11-35kW``. Their previous 0.5–2% inputs
produced implausible default consumption of 25–104 L/100 km in 2025.
``Motorcycle >35kW`` retains its 24% efficiency; electric and human inputs are
unchanged. This repairs the parameter defect, but does not establish empirical
calibration of the affected classes.

Basis and uncertainty
---------------------

The restored values come from `repository commit 6ed72b3
<https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_two_wheeler/commit/6ed72b3e0f5a29893212a8e8df4e0b501e96d2cc>`_,
before the September 2024 calibration introduced the low inputs:

* 2000, 2010 and 2020: 0.18.
* 2030: 0.1873309921; 2040: 0.1949605589; 2050: 0.2029008607.
* 2025: 0.1836654961, the linear midpoint of 2020 and 2030.

The existing triangular distribution is retained with bounds at 75% and 125%
of each mode. These are engineering uncertainty bounds, not a statistical
confidence interval. The future curve is a scenario assumption, not a forecast
validated against measurements.

The historical records cite `Cox and Mutel (2018)
<https://doi.org/10.1016/j.apenergy.2017.12.100>`_. This review could not verify
the numerical 18% assumption in that paper's supplementary calculations. The
current records therefore identify it as a **restored provisional engineering
prior**. Manufacturer consumption alone cannot identify engine efficiency
independently of cycle, road load, mass, transmission and accessory losses.

The parameter is used as cycle-average fuel-to-shaft efficiency. It must not
be replaced directly by an engine's peak or idealized thermal efficiency. For
example, the `US EPA PERE motorcycle model (2005)
<https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1001D6I.TXT>`_ describes a 32–40%
thermal-efficiency term but models engine friction separately. That term is
not an independent measurement of the efficiency required here.

Completed default runs
----------------------

The audit uses the bundled, size-specific ``Two wheeler cycle``, default
vehicle inputs, country CH and its default petrol blend. It does not substitute
manufacturer masses or tune any other parameter. Values below are L/100 km;
``fuel consumption`` itself is returned in L/km.

.. list-table:: Default consumption before and after the correction
   :header-rows: 1

   * - Size
     - Previous 2025
     - Corrected 2020
     - Corrected 2025
     - Corrected 2030
   * - Moped <4kW
     - 25.38
     - 1.416
     - 1.382
     - 1.349
   * - Scooter <4kW
     - 56.90
     - 1.588
     - 1.549
     - 1.511
   * - Scooter 4-11kW
     - 26.26
     - 2.926
     - 2.859
     - 2.796
   * - Motorcycle 4-11kW
     - 30.57
     - 3.427
     - 3.328
     - 3.234
   * - Motorcycle 11-35kW
     - 103.69
     - 5.821
     - 5.646
     - 5.477

All 30 before/after cases completed model sizing, inventory construction and
LCIA. Purchased fuel equals fuel energy divided by the blend's lower heating
value; supplier shares and fossil/non-fossil tailpipe CO2 agree with independent
fuel-specification balances. An additional 130 annual model cases, 2015–2040,
show a maximum absolute year-to-year consumption change of 0.614%. These are
numerical checks, not empirical validations.

Manufacturer evidence
---------------------

These are manufacturer-reported consumption figures, not independent road
measurements. Values were retrieved on 2026-10-08. The model column always uses
the generic **2025** class, so the older observations also have a year mismatch.
Reported WMTC results have not been matched to the exact trace, phase weighting,
test driving mass or cold-start treatment in the bundled cycle.

.. list-table:: Unmatched screening comparisons, L/100 km
   :header-rows: 1

   * - Vehicle / source
     - Class
     - Reported
     - Generic model
     - Difference
   * - `Piaggio Liberty 50, Euro 4 <https://wlassets.piaggio.com/wlassets/piaggio/gb/tech_spec/2020/Liberty_50/original/Liberty_50.pdf>`_
     - Scooter <4kW
     - 2.801 (35.7 km/L, WMTC)
     - 1.549
     - -44.7%
   * - `Honda PCX125, 2025 <https://hondanews.eu/gb/en/motorcycles/media/pressreleases/506369/25ym-honda-pcx125-press-kit>`_
     - Scooter 4-11kW
     - 2.1 (WMTC)
     - 2.859
     - +36.2%
   * - `Honda CB125R, 2024 <https://hondanews.eu/eu/en/motorcycles/media/pressreleases/472259/2024-honda-cb125r>`_
     - Motorcycle 4-11kW
     - 2.198 (45.5 km/L, WMTC)
     - 3.328
     - +51.4%
   * - `Honda CB125F, 2024 <https://hondanews.eu/eu/en/cars/media/pressreleases/470198/24ym-honda-cb125f>`_
     - Motorcycle 4-11kW
     - 1.4 (WMTC; see discrepancy below)
     - 3.328
     - +137.7%
   * - `Honda CB500 Hornet, 2024 <https://hondanews.eu/eu/en/motorcycles/media/pressreleases/452842/24ym-honda-cb500-hornet>`_
     - Motorcycle 11-35kW
     - 3.5 (WMTC)
     - 5.646
     - +61.3%
   * - `Yamaha MT-03, 2025 <https://cdn2.yamaha-motor.eu/prod/product-assets/2025/MT320/Factsheets/2025-MT320_en-GB.pdf>`_
     - Motorcycle 11-35kW
     - 4.0 (cycle unspecified in sheet)
     - 5.646
     - +41.1%

Piaggio's sheet sits in a 2020 source directory and describes Euro 4; it does
not specify a model year. For the CB125F, the English specifications give
1.4 L/100 km; the `French press kit
<https://hondanews.eu/fr/fr/motorcycles/media/pressreleases/470641/dossier-de-presse-honda-cb125f-2024>`_
gives 1.49 in its narrative and 1.4 in its table. The catalog records the
conflict. Neither value changes the conclusion that this class needs further
vehicle-specific review. No suitable moped observation was established here.

The observations support rejecting the old consumption scale. They do **not**
validate the restored default precisely: several residuals remain large and
some exceed what the retained efficiency uncertainty alone can explain.
Further calibration needs matched vehicles and cycles before altering the prior.
No measurement-error target or fitted efficiency was imposed in this correction.

Reproduction and scope
----------------------

The package includes :download:`the original records and correction provenance
<../carculator_two_wheeler/data/petrol_efficiency_provenance.json>`. This supersedes
only the affected petrol engine efficiencies in the earlier 2025/temporal
provenance; those older files remain historical records.

With matching source checkouts installed, run from this repository::

   python scripts/validate_petrol_efficiency.py --output /tmp/petrol-audit.json
   python -m pytest tests/test_petrol_efficiency.py

The script runs offline using the :download:`source catalog
<../tests/fixtures/petrol_consumption_sources.json>`. Its :download:`recorded model
and inventory results <_static/petrol_efficiency_audit.json>` include actual fuel
and CO2 exchanges. Tests additionally cover all five sizes at 2020/2025/2030
with three efficiency samples and fuel blends ranging from fossil petrol to
bioethanol. Their broad consumption envelope is a regression guard, not a
calibration acceptance criterion.

The electric-bicycle cost defect was subsequently addressed in :doc:`bicycle_costs`;
battery range/capacity/mass qualification remains a separate open issue.
Custom string labels on the sample coordinate also
failed a completed two-wheeler run during this review; the shared energy output
uses positional sample coordinates. These tests use the normal numeric sample
coordinates. No unrelated model or cost repair is included here.

Software verification for this correction
-----------------------------------------

On 2026-10-08 the two-wheeler suite passed 21 tests with the existing negative
bicycle-cost test marked as an expected failure. Fresh installed-artifact
verification passed the same 21 tests and 231 shared-utility tests; 92 shared
tests requiring the other three vehicle packages were skipped in this two-package
environment. Wheels, sdist-built wheels, resource hashes, dependencies and
offline core-only model/LCIA runs passed. Sphinx built with eight existing API
documentation warnings. These local macOS/Python 3.12 results do not certify
hosted CI or conda builds. The older five-package release record in
:doc:`release` predates this correction.
