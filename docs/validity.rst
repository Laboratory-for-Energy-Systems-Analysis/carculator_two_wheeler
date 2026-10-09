.. _validity:

Two-wheeler calibration and validation
======================================

The two-wheeler model uses component inventories, engineering assumptions and
legacy owner-reported fuel/electricity inputs described in :doc:`modeling`.
Those input sources are not a held-out, cycle-matched validation set for the
current model. Passenger-car registration data and car curb-mass plots do not
validate motorcycles, scooters or bicycles; the former copied claims have
been removed from this page.

.. _charging-cost-accounting:

Charging cost accounting
------------------------

Electricity running costs use grid purchases: ``electricity consumption`` in
kWh/km times the electricity tariff. Grid consumption already includes both
battery-charge and charger losses; neither efficiency is applied again when
billing that electricity. Previously the cost formula omitted charger losses.
At 90% charger efficiency it understated the electricity component by 10%; at
80% efficiency it understated it by 20%. This correction changes costs, while
preserving vehicle energy demand, inventory electricity exchanges and LCIA.

BEVs use this grid-based calculation. Other powertrains retain their existing
fuel-cost convention. Tariffs and charging-efficiency assumptions have not
been refitted.

Two-wheeler costs remain per vehicle-km. The default Swiss 2025
``Motorcycle 11-35kW`` BEV costs approximately EUR 1.91/100 km for electricity,
corrected from EUR 1.72/100 km.

Completed model/inventory checks and the shared billing contract are described
in the `shared charging-cost validation <https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_utils/blob/master/docs/validity.rst#charging-cost-accounting>`_.


Status of the 2025 review
-------------------------

Two-wheelers received the shared energy-accounting repairs, explicit 2025
inputs and consistent temporal extensions. The 118-observation measurement
catalog used for the recent paired comparisons covers cars, buses and trucks;
it does **not** establish new empirical two-wheeler calibration. In particular,
no new two-wheeler efficiency or auxiliary parameter was fitted to consumption.
The subsequent :doc:`petrol_efficiency` review restores a historical engineering
prior and adds six manufacturer screening observations; it does not fit a
new efficiency to those observations.

Analytical and model tests cover energy boundaries, regeneration, input
validation, unavailable configurations, and human-only and combustion-only
scopes. The annual audit includes a petrol moped, an electric scooter and an
electric bicycle over 2015–2040. These runs test numerical consistency, not
agreement with new road or laboratory measurements.

.. list-table:: Temporal checks on the unchanged standard cycle
   :header-rows: 1

   * - Vehicle
     - Boundary and unit
     - 2020
     - 2025
     - 2030
   * - Electric scooter <4 kW
     - Charging AC, kWh/100 km
     - 2.498
     - 2.500
     - 2.502

A small increasing trajectory is retained when other inputs imply it; no
monotonic consumption target is imposed. The current availability policy
excludes ``Moped <4kW`` with ``BEV`` and BEVs through 2010. Zeroed consumption
for an unavailable configuration is not evidence of physical efficiency.
Human metabolic energy must not be interpreted as charging electricity.

Evidence still needed
---------------------

Useful validation needs measured rider/cargo mass, actual speed and grade,
wind or road-load information, accessory demand, battery state and temperature,
and a stated meter boundary. Pedal-assisted cases additionally need rider
power or assistance settings. Owner-reported range divided by nominal battery
capacity does not uniquely identify drivetrain efficiency or charging losses.

Results are therefore suitable for documented scenario modelling, with these
assumptions exposed, rather than a claim of universally validated 2025
consumption. See the `shared temporal audit <https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_utils/blob/master/docs/temporal_energy.rst>`_ and
`energy-accounting checks <https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_utils/blob/master/docs/energy_model_repairs.rst>`_.

Energy boundaries and time trends
---------------------------------

``TtW energy`` is kJ/km. For a BEV it represents net stored-energy depletion;
``model.battery_terminal_energy`` reports net terminal DC energy separately.
``electricity consumption`` is charging electricity in kWh/km. Multiplying it
by 100 gives kWh/100 km. A meter boundary must be identified before comparing
these outputs. Regeneration and battery/charger losses must not be counted twice.

The 2025 motor/inverter (0.90), electric transmission (0.97), charger (0.90)
and symmetric battery one-way (sqrt(0.97)) values are component priors in their
documented scopes, not universally measured efficiencies. For relevant hybrid
scopes, the independent motor peak/system-power ratio is 0.65. The earlier temporal
update preserved all then-current 2025 scalar values and uncertainty distributions;
the later petrol correction is documented in :doc:`petrol_efficiency`. Storage
and charger trends preserve relative legacy losses; newly explicit component
priors are extended across native years to avoid interpolating from missing
zero values. Historical estimates and future projections therefore change.

The earlier family audit completed 546 annual cases (21 configurations, 2015–2040),
including availability-masked historical cells. The former inputs caused 20
sizing failures in this grid. All 40 existing 2025 measurement-comparison runs
retain their energy use and driving mass exactly. These are consistency and
regression checks, not 546 empirical validations. See
`temporal method, plots and limitations <https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_utils/blob/master/docs/temporal_energy.rst>`_.

Reproducibility
---------------

The installed package includes :download:`2025 record provenance
<../carculator_two_wheeler/data/defaults_2025_provenance.json>` and
:download:`temporal provenance and original affected records
<../carculator_two_wheeler/data/temporal_energy_provenance.json>`. Overrides should use measured
vehicle-specific inputs where available. Retain source, year, cycle, driving
mass, meter boundary and uncertainty assumptions with each comparison.

With matching Python 3.12 sibling checkouts, run from ``carculator_utils``::

   python scripts/validate_energy_measurements.py --output /tmp/measurements-new
   python scripts/audit_energy_time_trends.py --output /tmp/temporal-new

The shared `measurement catalog and outputs <https://github.com/Laboratory-for-Energy-Systems-Analysis/carculator_utils/blob/master/docs/energy_measurements.rst>`_
record excluded observations as well as paired values. Multiple cycles of one
vehicle and AC/DC measurements from one run are not independent vehicles.

Petrol parameter correction
---------------------------

The five affected petrol classes now use the restored historical efficiency
prior (18.37% in 2025). The default ``Motorcycle 11-35kW`` / ``ICEV-p`` case
returns **1.797 MJ/km**, or **5.646 L/100 km**, instead of 33.0 MJ/km.
See :doc:`petrol_efficiency` for provenance, before/after inventory checks and
manufacturer screening comparisons. Several unmatched consumption residuals
remain large; this correction is not a claim of completed empirical calibration.
Publication remains pending maintainer review of the remaining known issues.

Cost validation
---------------

See :doc:`small_vehicle_costs` for the scoped scooter/moped repair and
:doc:`bicycle_costs` for the repair of negative electric-bicycle costs,
its market-price proxy, accounting regressions and remaining component-price
gaps. Energy/LCIA validation does not establish the accuracy of ownership costs.

The subsequent :doc:`heat_pump_costs` correction removes the cabin heat-pump
charge from default BEV purchase costs while preserving explicit monetary overrides.
The :doc:`kick_scooter_charger_costs` correction replaces the generic charger price
only for BEV kick-scooters, with a sourced provisional assumption and scoped tests.

Target-range overrides
----------------------

Two-wheeler target-range sizing now converges battery capacity, vehicle mass
and cycle energy together. Completed runs cover four chemistries, multiple
years and samples, all available BEV sizes, and battery/electricity inventory
coefficients. Capacity and pack-mass changes also propagate through consumption
and range. See :doc:`bev_sizing` for the method, override contracts and numerical
checks. This establishes software consistency, not new empirical calibration.

Battery replacement policy
--------------------------

The former mandatory extra battery has been removed for two-wheelers.
Replacement factors now allow zero when lifetime throughput is within the
configured cycle life. Production, disposal and replacement costs use the same
factor. See :doc:`battery_replacements` for completed inventory checks and the
retained fractional-allocation, upper-cap and calendar-ageing limitations.
This correction does not change consumption calibration or prove battery durability.
