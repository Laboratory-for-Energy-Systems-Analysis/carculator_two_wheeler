.. _validity:

Two-wheeler calibration and validation
======================================

The two-wheeler model uses component inventories, engineering assumptions and
legacy owner-reported fuel/electricity inputs described in :doc:`modeling`.
Those input sources are not a held-out, cycle-matched validation set for the
current model. Passenger-car registration data and car curb-mass plots do not
validate motorcycles, scooters or bicycles; the former copied claims have
been removed from this page.

Status of the 2025 review
-------------------------

Two-wheelers received the shared energy-accounting repairs, explicit 2025
inputs and consistent temporal extensions. The 118-observation measurement
catalog used for the recent paired comparisons covers cars, buses and trucks;
it does **not** establish new empirical two-wheeler calibration. In particular,
no new two-wheeler efficiency or auxiliary parameter was fitted to consumption.

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
scopes, the independent motor peak/system-power ratio is 0.65. The temporal
update preserves all 2025 scalar values and uncertainty distributions. Storage
and charger trends preserve relative legacy losses; newly explicit component
priors are extended across native years to avoid interpolating from missing
zero values. Historical estimates and future projections therefore change.

The family audit completes 546 annual cases (21 configurations, 2015–2040),
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
The family artifact verification passed 436 tests, with one existing expected
two-wheeler failure, plus offline wheel/source-distribution model and LCIA checks.
That software verification does not replace empirical validation.
