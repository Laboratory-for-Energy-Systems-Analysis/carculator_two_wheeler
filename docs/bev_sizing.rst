BEV battery sizing and range
============================

Battery mass, nominal capacity, driving mass and energy demand are coupled in
completed two-wheeler runs. This corrects the former target-range path, which
resized the battery after calculating vehicle mass and consumption. A reported
range could therefore use the energy demand of a lighter or heavier vehicle.

Sizing method
-------------

For a BEV range target, each iteration calculates vehicle/component masses and
cycle energy, then sizes the battery using:

.. math::

   C_{nominal}\;[\mathrm{kWh}] =
   \frac{R\;[\mathrm{km}]\;E_{stored}\;[\mathrm{kJ/km}]}{3600\;DoD}

Cell mass is nominal capacity divided by cell energy density (kWh/kg). Pack
mass is cell mass divided by the cell mass share. The next iteration includes
that pack in curb and driving mass and recomputes power and energy demand.
Convergence checks driving and battery mass separately for every vehicle,
year and sample, with relative tolerance ``1e-5`` and the shared bounded
``max_iterations`` limit. Failure raises ``ConvergenceError`` with coordinates.

A fixed curb mass also requires convergence of the glider mass: otherwise the
fixed total can conceal an inconsistent component sum. Replacements, costs,
emissions and inventories are calculated from the completed sizing result.
The sizing repair itself did not change replacement or component-efficiency
assumptions. The subsequent :doc:`battery_replacements` correction removes the
mandatory extra pack for two-wheelers.

Selecting the input constraint
------------------------------

Start with fresh static inputs for each scenario:

.. code-block:: python

   from carculator_two_wheeler import (
       TwoWheelerInputParameters,
       TwoWheelerModel,
       fill_xarray_from_input_parameters,
   )

   inputs = TwoWheelerInputParameters()
   inputs.static()
   _, array = fill_xarray_from_input_parameters(
       inputs,
       scope={"size": ["Scooter <4kW"], "powertrain": ["BEV"], "year": [2025]},
   )
   key = ("BEV", "Scooter <4kW", 2025)

   # Range-driven sizing, with an explicit chemistry.
   model = TwoWheelerModel(
       array,
       energy_storage={"electric": {key: "LFP"}},
       target_range={key: 100},  # km
   )
   model.set_all()
   print(model["electric energy stored"])  # nominal kWh
   print(model["electricity consumption"] * 100)  # charging kWh/100 km

For fixed nominal capacity, use
``energy_storage={"capacity": {key: 4}, "electric": {key: "LFP"}}`` instead
of ``target_range``. For fixed pack mass, set
``array.loc[dict(parameter="energy battery mass")] = 20`` (kg) before constructing
the model, and omit both capacity and range overrides. Scope that assignment
when the input array contains other vehicles or years.

A range target takes precedence over a capacity override for the same BEV;
a capacity override takes precedence over input pack mass. ``None`` range
targets leave the vehicle's existing sizing constraint in place. Overrides
preserve caller-owned arrays and dictionaries and do not resize other vehicles.

With a fixed range, a heavier chemistry generally increases energy demand and
the required capacity. With fixed pack mass, chemistry changes capacity and
range; consumption can remain identical because total mass is unchanged.
``target_mass={key: 100}`` fixes curb mass in kg by adjusting the glider, while
``energy_consumption={key: 90}`` fixes stored-energy demand in kJ/km. Either can
legitimately remove the chemistry dependence of consumption and required
capacity. Consumption overrides are applied to an existing energy trace before
battery-loss accounting, so their public stored-energy boundary is preserved.

Numerical verification
----------------------

For the default 2025 scooter below 4 kW on its standard cycle, a 200 km target
produces the following results. The former path reported 200 km, but a fresh
run using its 5.373 kWh pack returned only 192.9 km.

.. list-table:: Completed range-constrained scenarios
   :header-rows: 1

   * - Output
     - Former NMC-811 result
     - Corrected NMC-811
     - Corrected LFP
   * - Nominal capacity, kWh
     - 5.373
     - 5.594
     - 5.894
   * - Pack mass, kg
     - 25.56
     - 26.60
     - 40.93
   * - Curb mass, kg
     - 77.75
     - 88.35
     - 102.68
   * - Charging electricity, kWh/100 km
     - 2.500
     - 2.603
     - 2.743

Fresh capacity-constrained runs reproduce the corrected range, mass, power and
consumption within the sizing tolerance. These are consistency checks, not
measurements or proof that a particular commercial scooter can accommodate
these packs. No empirical calibration parameters were changed.

``tests/test_bev_sizing.py`` covers:

* LFP, NMC-111, NMC-622 and NMC-811 across bicycles, small scooters and motorcycles,
  2020/2025/2030, and two labelled rider/cargo samples;
* all nine currently available BEV size classes in 2025;
* independent component-mass and usable-energy balances, fresh fixed-capacity
  runs, and increasing capacity or pack mass;
* fixed curb mass and consumption, scoped overrides, precedence, unavailable
  configurations, input preservation and bounded convergence;
* completed static-background LCIA and the actual inventory coefficients for
  charging electricity and chemistry-specific battery supply, including the
  existing replacement factor.

The before/after default audit covered all ten sizes, three powertrains and
2020/2025/2030: every parameter output was unchanged without sizing overrides.
This grid includes unavailable combinations and is a software regression check.
The usual availability masks still apply; an excluded vehicle's zero energy
output does not demonstrate that it can meet a target range.

Run the focused regressions with matching shared utilities installed::

   python -m pytest tests/test_bev_sizing.py
