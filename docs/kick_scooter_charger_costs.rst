Kick-scooter charger cost
=========================

The 2026-10-08 correction replaces the generic BEV charger price for
``Kick-scooter / BEV`` with a **EUR 70** provisional default and triangular
engineering uncertainty from **EUR 40 to EUR 100**. The parameter retains its
legacy name, ``battery onboard charging infrastructure cost``, for API
compatibility. For this class it represents the vehicle charger cost proxy;
the label does not establish that the charger is physically carried onboard.

Evidence and uncertainty
------------------------

The `NIU EU official replacement-parts store
<https://shopeu.niu.com/collections/spare-parts>`_ listed these euro retail prices
when retrieved on 2026-10-08:

* KQi 100 Series Charger: EUR 39.99, listed as sold out.
* KQi2 Pro & KQi 200 Charger: EUR 69.99, listed with an add-to-cart option.
* KQi Super Charger: EUR 79.99, listed as sold out.

The mode rounds the middle listing to EUR 70 and the lower bound rounds the
lowest listing to EUR 40. The EUR 100 upper bound is an engineering allowance
above the observed maximum, not a measured confidence bound. Three listings
from one manufacturer do not identify a market distribution. Their use for a
generic vehicle with unmatched charger voltage, power and equipment is a
provisional assumption.

These are **replacement retail prices**, not OEM supply quotations. Their price
year is undated; current prices observed in 2026 are used as a proxy for the
2025 model without inflation adjustment. No separate VAT or shipping adjustment
has been made. The packaged provenance records the observations and assumptions.

Time, accounting and scope
--------------------------

The same EUR 70 mode and EUR 40-100 bounds apply at all native years from 2000
to 2050. This constant scenario assumption prevents an isolated 2025 change;
it is not a historical price reconstruction or a nominal-price forecast.
Availability masking is unchanged. Other cost components retain their existing
trajectories and price bases.

The shared purchase-component list applies this cost once, without markup.
The retail-price proxy is therefore entered directly. The glider, motor,
battery and replacement assumptions are not refitted to offset the correction.
Other vehicle classes keep their own existing charger records through a
disjoint input-scope split.

This is a monetary-input change. Charger mass, charging efficiencies, driving
mass, energy use and charger inventory exchanges are unchanged. Their physical
interpretation requires separate qualification; a price observation does not
validate those physical parameters. Explicit user cost overrides remain valid.

Completed-run results
---------------------

Recorded kick-scooter results immediately after the charger correction, in
EUR per vehicle and EUR per vehicle-kilometre. The later
:doc:`battery_replacements` correction further reduces total costs; purchase
costs in this table are unchanged:

.. list-table::
   :header-rows: 1
   :widths: 12 22 22 22 22

   * - Year
     - Previous charger
     - Previous purchase
     - Corrected purchase
     - Corrected total/km
   * - 2020
     - 174.13
     - 389.62
     - 285.49
     - 0.21122
   * - 2025
     - 164.35
     - 374.26
     - 279.91
     - 0.20450
   * - 2030
     - 154.57
     - 360.53
     - 275.96
     - 0.19973

The corrected charger cost is EUR 70 in each row. For 2025, purchase decreases
by EUR 94.35, from EUR 374.26 to EUR 279.91. The resulting complete vehicle price
is not an independent calibration target or a validated market price. Its
other component assumptions, short 1,785 km lifetime and maintenance rate still
limit interpretation of the total cost per kilometre.

The audit completed **24 before/after model, inventory and LCIA cases** in
2020, 2025 and 2030: six kick-scooter cases and 18 control cases covering
``Bicycle <25``, ``Scooter <4kW`` and ``Motorcycle >35kW`` BEVs. Only the target
charger, purchase, amortised purchase and total cost outputs change. All other
model parameters, all control vehicles, inventory matrices and LCIA results
are identical. Another **26 annual kick-scooter runs** from 2015 through 2040
check the constant charger prior and positive costs.

Regression tests cover the lower bound, mode and upper bound in completed
models, independent ten-year discounted repayment sums, seeded input sampling,
interpolation at every year from 2000 through 2050, and explicit overrides via
both arrays and input dictionaries. They do not claim every stochastic model
adjustment is seeded.

Reproduction and explicit scenarios
-----------------------------------

The installed package includes :download:`sources, assumptions and original
records <../carculator_two_wheeler/data/kick_scooter_charger_cost_provenance.json>`.
The :download:`recorded audit <_static/kick_scooter_charger_cost_audit.json>`
contains before/after results, annual runs and the input hash. Run offline::

   python scripts/validate_kick_scooter_charger_costs.py --output /tmp/charger-costs.json
   python -m pytest tests/test_kick_scooter_charger_costs.py

To override the cost, modify the input array before constructing the model::

   array.loc[dict(
       parameter="battery onboard charging infrastructure cost",
       size="Kick-scooter", powertrain="BEV", year=2025,
   )] = 123.45

A custom parameter dictionary is also supported. When specifying a deterministic
record, set ``amount`` and ``loc``, use ``uncertainty_type=1`` and omit triangular
bounds. Historical reports in :doc:`small_vehicle_costs` and :doc:`heat_pump_costs`
retain their earlier kick-scooter totals. Their scripts isolate their respective
changes against currently installed inputs, so a rerun also reflects this new
charger prior. Charger assumptions for other classes remain open.
