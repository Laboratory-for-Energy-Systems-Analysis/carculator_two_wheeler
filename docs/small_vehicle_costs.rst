Small-vehicle cost correction
=============================

The 2026-10-08 repair replaces the negative-intercept glider fit for
``Kick-scooter / BEV``, ``Moped <4kW / ICEV-p`` and both ``BEV`` and ``ICEV-p``
``Scooter <4kW``. At their default masses, the old ``16 * mass - 900`` inputs
produced negative glider and maintenance costs. The kick-scooter also had a
negative purchase cost. The repair changes only these input scopes; it does
not clip cost outputs or change the cost equations, energy model or inventory.

Evidence and assumptions
------------------------

These are **provisional cost priors**, not measured component bills or an
independently validated ownership-cost model. Prices were retrieved on
2026-10-08. Only the Piaggio source has a documented 2025 price date; the other
undated listings are proxies for the 2025 model with no inflation adjustment.
Vehicle masses, battery sizes, equipment and national markets are not matched.

* `Decathlon/Oxelo T7XL <https://www.decathlon.fr/p/trottinette-adulte-t7xl-noire/12329/c382c344m8377410>`_:
  EUR 119.99 for a 5.6 kg non-electric scooter, excluding any delivery charge.
  Its complete mechanical assembly supplies a mass-proportional proxy for the
  kick-scooter glider. This is not the price of an electric scooter.
* `Mash Fifty 50 cc <https://www.mash-motors.fr/en/50cc/46326-10806-mash-fifty-50-cc.html>`_:
  EUR 2,099 including tax, excluding registration and commissioning. Its
  reported 2.1 kW and 105 kg describe the source vehicle, not the lighter
  generic moped model. The price anchors that class provisionally.
* `NIU NQi Sport Standard Range <https://france.niu.com/collections/best-selling-collection/products/nqi-sport>`_:
  EUR 1,999 base price; the EUR 100 displayed reservation amount is only a
  deposit. The EUR 18.26 environmental contribution and EUR 129 registration
  charge are excluded from this anchor.
* `Piaggio October 2025 German price list <https://wlassets.piaggio.com/wlassets/piaggio/de/pricelist/2025/Preisliste_PIAGGIO_10-2025/original/Preisliste_PIAGGIO_10-2025.pdf?1759918272054=>`_:
  Liberty 50 is EUR 2,649 including EUR 208 ancillary charges on PDF page 3.
  Subtracting that separately stated charge gives the EUR 2,441 vehicle anchor;
  VAT is not removed.

The kick-scooter slope is ``119.99 / (5.6 * 1.2) = 17.85565 EUR/kg``.
For the other three classes, subtract the **frozen default 2025 non-glider
component costs** from the vehicle anchor, then divide the residual by the
reference glider mass and 1.2 reference markup. The resulting slopes are
26.98811, 19.46037 and 26.62685 EUR/kg for the petrol moped, electric small
scooter and petrol small scooter, respectively. All four intercepts are zero.
The packaged provenance lists every deducted component and its value.

This residual method keeps the existing battery, motor, tank, charger,
exhaust-treatment and lightweighting costs separate. It does not identify a
factory glider cost: the residual depends on those inherited component
assumptions. The 1.2 division prevents applying the model's reference markup
twice to a retail anchor; VAT and dealer margins are not separately estimated.
The coefficients are frozen input data. Changing component costs subsequently
changes the purchase total; no runtime refitting absorbs those changes.

The inherited **EUR 300 heat-pump charge** was deliberately excluded from the
calibration residual and has since been removed by :doc:`heat_pump_costs`.
Without refitting the glider, the default electric scooter purchase total is
now EUR 1,999. The subsequent :doc:`kick_scooter_charger_costs` correction sets
the kick-scooter charger to EUR 70 and its purchase total to EUR 279.91. The
other classes retain their charger assumptions. Complete electric prices still
require qualification. Matching the petrol price anchors
by construction is a calibration result, not independent validation.

Time and uncertainty
--------------------

Each new slope and zero intercept is carried unchanged over all native years
(2000, 2010, 2020, 2025, 2030, 2040 and 2050), so this repair introduces no
isolated 2025 coefficient step. This is a constant scenario assumption, not
historical or forecast nominal pricing. The other cost components retain their
legacy price bases and trajectories. Their common currency year still needs
review; the complete purchase series can therefore vary with year.

Each native year's original relative triangular slope bounds is preserved.
These bounds represent engineering uncertainty, not a confidence interval
inferred from four manufacturer observations. Completed static models test the
lower bound, mode and upper bound separately. This is not a full stochastic
qualification of all cost inputs or all possible user overrides.

Completed-run results
---------------------

Recorded 2025 values immediately after the glider correction (EUR per vehicle
and EUR per vehicle-kilometre). This table predates :doc:`heat_pump_costs`,
which reduces BEV purchase totals by another EUR 300:

.. list-table::
   :header-rows: 1
   :widths: 34 16 16 17 17

   * - Vehicle / powertrain
     - Previous purchase
     - Corrected purchase
     - Maintenance/km
     - Total cost/km
   * - Kick-scooter / BEV
     - -421.33
     - 674.26
     - 0.00421
     - 0.44216
   * - Moped <4kW / ICEV-p
     - 465.20
     - 2099.00
     - 0.02599
     - 0.17014
   * - Scooter <4kW / BEV
     - 998.92
     - 2299.00
     - 0.01971
     - 0.18149
   * - Scooter <4kW / ICEV-p
     - 685.13
     - 2441.00
     - 0.03236
     - 0.19914

The high kick-scooter cost per kilometre also reflects its unchanged default
lifetime of 1,785 km. Maintenance retains the existing annual glider-cost
fractions (2.5% for BEV, 3% for petrol); these rates have not been calibrated to
repair invoices. Total costs include amortised purchase, midpoint-discounted
battery replacement, maintenance and energy under the existing accounting.

The audit completed **24 before/after model, inventory and LCIA cases** across
2020, 2025 and 2030. Driving mass, energy, inventory matrices and LCIA results
were identical. **104 annual model cases** cover 2015-2040; glider coefficients
are constant, while inherited component trends remain visible in the report.
Independent ten-year cash-flow checks verify capital repayment and maintenance.
Separate repricing checks show battery and motor price changes still reach the
purchase total without changing the glider cost.

Reproduction and remaining limits
---------------------------------

The installed package contains :download:`sources, assumptions, frozen component
values and original records <../carculator_two_wheeler/data/small_vehicle_cost_provenance.json>`.
Original multi-size records are split into disjoint scopes. Earlier petrol,
bicycle and temporal provenance remains a historical record. Run::

   python scripts/validate_small_vehicle_costs.py --output /tmp/small-vehicle-costs.json
   python -m pytest tests/test_small_vehicle_costs.py tests/test_bicycle_costs.py

The offline audit reconstructs the previous inputs from the packaged provenance.
Its :download:`recorded results <_static/small_vehicle_cost_audit.json>` include
complete purchase breakdowns, annual costs and unchanged inventory/LCIA checks.
Those recorded totals predate the heat-pump correction. Rerunning this audit
isolates the glider change against the currently installed defaults.

Charger costs for other classes, complete e-bike costs and a common currency-year
basis remain evidence gaps. Human bicycle inputs have since been populated
(:doc:`bicycle_costs`); battery coupling and named samples have been repaired
(:doc:`bev_sizing`, :doc:`validity`). Historical results above isolate this earlier
cost change and do not constitute new fuel-consumption calibration.
