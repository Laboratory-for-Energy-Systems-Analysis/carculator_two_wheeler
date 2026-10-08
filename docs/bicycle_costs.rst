Bicycle cost correction
=======================

The 2026-10-08 correction replaces the negative-intercept glider-cost fit for
``Bicycle <25``, ``Bicycle <45`` and ``Bicycle cargo`` with ``BEV``. The old
``16 * glider base mass - 900`` relationship gave a negative mechanical-bicycle
cost at all three default masses. This propagated into negative maintenance
and, for two classes, negative purchase and total costs. No output clipping or
runtime minimum cost is used in this repair.

Evidence and assumptions
------------------------

`ZIV's 2025 market report, slide 18
<https://www.ziv-zweirad.de/wp-content/uploads/2026/03/Market-Data-Bicycle-Industry-2025.pdf>`_
(published 11 March 2026, retrieved 8 October 2026) reports a German average
non-electric bicycle sales price of **EUR 500** across all channels. The gross
retail price is used as a proxy for a complete mechanical bicycle: frame,
wheels, brakes and mechanical drivetrain, excluding an electric motor and
traction battery. This transfer is an engineering assumption; ZIV does not
publish an e-bike glider bill of materials.

The reference mass is the existing model's 12 kg human-powered bicycle glider;
the reference markup is 1.2. Neither comes from the market survey. The corrected
coefficients are:

.. math::

   a = \frac{500}{12 \times 1.2} = 34.722222\ \mathrm{EUR/kg},\qquad b = 0.

The existing calculation remains ``(a * glider base mass + b) * markup factor``.
Dividing by the reference markup avoids counting it twice. This decomposition
does not identify factory production cost, dealer margins or VAT separately.
The slope's triangular relative bounds are preserved at each native year; the
intercept is deterministic zero. These bounds remain engineering uncertainty,
not a confidence interval for market prices.

The same coefficients apply at every native year from 2000 to 2050, including
2025. This is a constant-real-2025-EUR assumption for this component, not a
historical nominal-price reconstruction or a future price forecast. Other
legacy cost components have not been converted to a common price year.
Mass-proportional transfer to electric, speed and cargo bicycles is provisional:
quality and equipment can matter more than mass. The source does not establish
these class-specific component costs independently.

Completed runs
--------------

Default 2025 outputs, with the existing motor, battery, charging, financing and
maintenance assumptions:

.. list-table:: Effect of the correction
   :header-rows: 1

   * - BEV size
     - Previous purchase, EUR
     - Corrected purchase, EUR
     - Corrected maintenance, EUR/year
     - Previous total, EUR/vkm
     - Corrected total, EUR/vkm
   * - Bicycle <25
     - -188.98
     - 1,250.49
     - 16.67
     - -0.01499
     - 0.09621
   * - Bicycle <45
     - -76.79
     - 1,430.08
     - 19.79
     - -0.00262
     - 0.07498
   * - Bicycle cargo
     - 252.09
     - 2,185.82
     - 39.58
     - 0.02032
     - 0.16971

The calculated annual maintenance values retain the existing 2.5% of glider-cost
assumption; this correction does not empirically validate that percentage.
The package's total cost includes amortised purchase, discounted component
replacement, maintenance and energy. It is not a comprehensive household
ownership budget including insurance, theft, accessories and resale value.

All 18 before/after cases at 2020, 2025 and 2030 completed model and LCIA runs;
driving mass, energy and LCIA results were unchanged. Tests check positive costs
at the lower/mode/upper glider-slope assumptions and independently verify capital
repayment and maintenance accounting. The original negative-cost regression now
passes normally. Annual runs from 2015 to 2040 cover another 78 model cases.
No special 2025 coefficient jump is introduced.

Remaining evidence gaps
-----------------------

ZIV reports **EUR 2,550** for the average complete e-bike in 2025. The generic
``Bicycle <25`` purchase result is still about **51% lower**. This comparison
has unmatched quality, product mix and cost boundaries; it is recorded as
screening evidence, not an acceptance test. The repair establishes positive,
traceable mechanical-bicycle costs, not a calibrated complete e-bike price.
Motor, battery and charger prices and their common currency-year basis need
separate review before claiming representative ownership costs.

The original fit remains for kick-scooters, mopeds and small scooters, which
can still have negative glider/maintenance costs. Human-only bicycle cost inputs
also remain incomplete. Those are separate scopes from this approved electric-
bicycle correction. Battery coupling and sample-label limitations documented
in :doc:`validity` and :doc:`petrol_efficiency` are unaffected.

Reproduction
------------

The installed package includes :download:`source, assumptions and original input
records <../carculator_two_wheeler/data/bicycle_cost_provenance.json>`. Original
multi-size records are split into disjoint bicycle and remaining-vehicle scopes;
no overlapping-record precedence is used to implement the change. The earlier
2025, temporal and petrol audits retain their historical provenance.

With matching source packages installed, run from this repository::

   python scripts/validate_bicycle_costs.py --output /tmp/bicycle-costs.json
   python -m pytest tests/test_bicycle_costs.py tests/test_model.py

The audit works offline and reconstructs the previous data from the packaged
provenance. Its :download:`recorded results <_static/bicycle_cost_audit.json>`
include before/after costs, annual results, market screening and LCIA checks.

Software checks
---------------

The full two-wheeler source suite passed 29 tests on 2026-10-08, with no
expected failures. Sphinx built successfully with eight pre-existing API
documentation warnings. Fresh installed-artifact verification passed 29 two-wheeler and 231 shared
tests, with 92 shared tests skipped because the other three vehicle packages
were not installed. Wheel/sdist resource checks, dependency checks and offline
core-only model/LCIA runs passed. These local macOS/Python 3.12 checks do not
certify hosted CI or conda builds; historical reports in :doc:`release` and :doc:`petrol_efficiency`
predate this cost correction.
