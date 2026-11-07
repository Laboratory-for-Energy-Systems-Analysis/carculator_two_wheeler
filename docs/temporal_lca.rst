Calendar-year lifecycle impacts
===============================

``carculator_two_wheeler`` can optionally distribute its completed foreground
inventory over calendar years. The ordinary lifetime LCIA and exports are not
changed; the temporal result is an additional view of the same exchanges.

Quick start
-----------

Complete the model and inventory first::

   from carculator_two_wheeler import (
       InventoryTwoWheeler,
       TwoWheelerInputParameters,
       TwoWheelerModel,
       fill_xarray_from_input_parameters,
   )

   inputs = TwoWheelerInputParameters()
   inputs.static()
   _, array = fill_xarray_from_input_parameters(
       inputs,
       scope={
           "size": ["Scooter <4kW", "Motorcycle 11-35kW"],
           "powertrain": ["BEV"],
           "year": [2025],
       },
   )
   model = TwoWheelerModel(array)
   model.set_all()
   inventory = InventoryTwoWheeler(model, scenario="SSP2-NPi")

   schedule = inventory.lifecycle_schedule()
   impacts = inventory.calculate_temporal_impacts()
   audit = inventory.temporal_coverage()

``year`` is the vehicle cohort year and ``calendar_year`` is the event year.
Results distinguish manufacturing, use, maintenance, replacement and end of
life. The default normalization reports one vehicle; select
``normalization="functional_unit"`` for lifetime vehicle-kilometres.

Maintenance frequency by vehicle type
-------------------------------------

.. list-table:: Default two-wheeler maintenance timing
   :header-rows: 1
   :widths: 38 18 44

   * - Vehicle and powertrain
     - Frequency
     - Cell-specific distance threshold
   * - Human-powered bicycle
     - Every 1 year
     - ``1 * kilometers per year``
   * - Electric bicycle and cargo bicycle
     - Every 1 year
     - ``1 * kilometers per year``
   * - Petrol moped, scooter and motorcycle
     - Every 1 year
     - ``1 * kilometers per year``
   * - Electric motorcycle
     - Every 1 year
     - ``1 * kilometers per year``
   * - Electric road scooter
     - Every 2 years
     - ``2 * kilometers per year``
   * - Electric kick-scooter
     - Every 2 years
     - ``2 * kilometers per year``

These are temporal allocation assumptions, not maintenance instructions for a
specific product. Published manufacturer schedules vary by inspection item,
distance, time and vehicle class. The model uses annual timing for bicycles and
motorcycles and a two-year convention for electric scooters, always converted
with the vehicle cell's assumed annual mileage.

The frequency only schedules a burden that exists in the inventory. Current
petrol two-wheelers and bicycles have explicit lifetime maintenance exchanges;
electric scooters and motorcycles do not. Their default service calendar is
still visible in ``lifecycle_schedule()``, but it creates no maintenance impact
until an explicit exchange exists. This prevents a timing assumption from
inventing inventory.

A threshold reached at year end belongs to that operating year: annual service
starts in the cohort year and a two-year interval first appears in the next
year. A fractional allocation in the final partial year conserves the lifetime
maintenance total and is not a fractional workshop visit.

Timing by component and exchange type
-------------------------------------

.. list-table:: Two-wheeler temporalization contract
   :header-rows: 1
   :widths: 24 19 37 20

   * - Component or burden
     - Lifecycle stage
     - Default timing
     - Recurrence basis
   * - Bicycle, scooter or motorcycle glider and lightweighting
     - Manufacturing
     - Cohort year
     - Once per vehicle
   * - Combustion engine, electric motor, inverter, converter and fuel tank
     - Manufacturing
     - Cohort year
     - Once per vehicle
   * - Initial traction battery
     - Manufacturing
     - Cohort year
     - Once per electric vehicle
   * - Traction-battery replacements
     - Replacement
     - Battery distance/calendar threshold when available; otherwise battery
       throughput from stored energy and cycle life
     - Modelled count, including fractional legacy counts
   * - 100 W, 500 W or 3 kW charging station
     - Manufacturing
     - Cohort year as one allocated charger exchange
     - No independent charger-replacement event is exposed
   * - Petrol two-wheeler maintenance
     - Maintenance
     - Every operating year
     - Annual mileage threshold
   * - Human and electric bicycle maintenance
     - Maintenance
     - Every operating year
     - Annual mileage threshold
   * - Electric scooter and motorcycle maintenance
     - Maintenance
     - Calendar available, but current exchange is zero
     - Two years for scooters; one year for motorcycles
   * - Electricity and petrol supply
     - Use
     - Every operating year, including exact distance in the final partial year
     - Per vehicle-kilometre
   * - Exhaust, abrasion and noise emissions
     - Use
     - Every operating year where the inventory contains the flow
     - Per vehicle-kilometre
   * - Road construction and maintenance
     - Use
     - Every operating year where nonzero; existing lightweight-vehicle
       reductions are retained
     - Per vehicle-kilometre
   * - Used replacement battery
     - End of life
     - Each battery-replacement year
     - One disposal share per replacement
   * - Bicycle/e-bike treatment and electric-scooter dismantling
     - End of life
     - One year after the final operating year
     - Once at final end of life
   * - Petrol scooter and motorcycle disposal
     - Supplier-embedded boundary
     - Remains with the production supplier in the cohort year
     - No duplicate explicit disposal event

Wear-part replacements are not separate component events. Their effects remain
in initial production, maintenance proxies or annual wear emissions according
to the existing inventory boundary. Likewise, charger lifetime is not inferred
when only one allocated charging-station exchange is available.

Policy overrides
----------------

Manufacturing and maintenance timing can be customized::

   from carculator_utils import TemporalPolicy

   policy = TemporalPolicy(
       manufacturing={
           "vehicle": {-1: 0.7, 0: 0.3},
           "battery": {-1: 0.4, 0: 0.6},
       },
       maintenance_interval_years={
           "BEV": 2,
           "Human": 1,
           "default": 1,
       },
       end_of_life_offset=1,
   )
   impacts = inventory.calculate_temporal_impacts(policy)

Selectors are resolved from the full ``combined_dim`` label, powertrain,
vehicle family and ``"default"``. An explicit kilometre threshold takes
precedence::

   distance_based = TemporalPolicy(
       service_intervals={"maintenance": 10_000}
   )

Annual backgrounds, electricity and limitations
------------------------------------------------

Characterization factors and national electricity are interpolated for each
event year. ``background_horizon="hold"`` uses the nearest endpoint and
``"error"`` rejects years beyond the available background. The electricity
endpoint policy is configured with ``"temporal electricity horizon"``.

Only exposed direct foreground exchanges can be dated. Supplier-embedded
delivery, dismantling or disposal remains with the supplier event. Fuel shares
remain those selected for the cohort, while electricity linked to preparation
is updated annually. Calendar assignment is not impact discounting or dynamic
atmospheric-fate modelling.

Inspect ``inventory.lifecycle_events.to_dataset()`` and
``inventory.temporal_coverage(policy)`` for the exchange ledger, resolved
maintenance frequency, horizons and event-year range. The shared
``carculator_utils`` calendar-year guide is the normative API reference.
