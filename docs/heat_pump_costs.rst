Heat-pump cost correction
=========================

The 2026-10-08 correction removes the inherited **EUR 300 cabin heat-pump
charge** from default BEV two-wheelers. All seven native-year records
(2000, 2010, 2020, 2025, 2030, 2040 and 2050) now use deterministic zero,
including the formerly triangular sampling distributions. Interpolation
therefore introduces no special 2025 step or residual sampled heat-pump cost.

Why this default changes
------------------------

This is a correction of the model's equipment scope, not a new market-price
calibration. ``TwoWheelerModel.calculate_ttw_energy()`` passes propulsion,
auxiliary demand and battery efficiencies to the shared energy model, without
cabin HVAC inputs. Its vehicle mass calculation includes no corresponding
cabin heat-pump equipment. The old cost records described passenger-car heating
and used ``Euro / car`` as their unit.

The shared ``purchase_cost_params.yaml`` includes ``heat pump cost`` in the
purchase total, but not in the marked-up components. Consequently the old
static charge entered purchase once as EUR 300, rather than EUR 360. Removing
it reduces annualized purchase and total cost per kilometre according to the
existing lifetime and interest-rate assumptions. Maintenance, battery
replacement and energy costs do not change.

The parameter remains in the input data and shared cost accounting. Only the
two-wheeler defaults change; no runtime rule forces a user's value to zero.
Battery thermal-management assumptions, charger prices, glider priors and
other vehicle packages are outside this correction. In particular, the
:doc:`small_vehicle_costs` glider residual deliberately excluded the heat-pump
charge and is not refitted to absorb its removal.

Default 2025 results
--------------------

All rows are BEV, with purchase in EUR per vehicle and total cost in EUR/vkm.

.. list-table::
   :header-rows: 1
   :widths: 34 22 22 22

   * - Size
     - Previous purchase
     - Corrected purchase
     - Corrected total/km
   * - Kick-scooter
     - 674.26
     - 374.26
     - 0.26136
   * - Bicycle <25
     - 1250.49
     - 950.49
     - 0.07678
   * - Bicycle cargo
     - 2185.82
     - 1885.82
     - 0.15028
   * - Bicycle <45
     - 1430.08
     - 1130.08
     - 0.06203
   * - Scooter <4kW
     - 2299.00
     - 1999.00
     - 0.16380
   * - Scooter 4-11kW
     - 1649.27
     - 1349.27
     - 0.10460
   * - Motorcycle 4-11kW
     - 1257.26
     - 957.26
     - 0.08691
   * - Motorcycle 11-35kW
     - 2597.98
     - 2297.98
     - 0.12357
   * - Motorcycle >35kW
     - 5367.16
     - 5067.16
     - 0.16016

These prices retain the existing battery, motor, charger and other cost
assumptions. They are not a claim of representative complete retail prices.
The remaining charger assumptions, human-only bicycle inputs and common
currency-year basis still need review. The short default kick-scooter lifetime
of 1,785 km continues to explain much of its high cost per kilometre.

Explicit scenarios
------------------

For a monetary scenario that includes a separate heat-pump cost, set the
parameter before constructing the model::

   from carculator_two_wheeler import (
       TwoWheelerInputParameters, TwoWheelerModel,
       fill_xarray_from_input_parameters,
   )

   inputs = TwoWheelerInputParameters()
   inputs.static()
   _, array = fill_xarray_from_input_parameters(
       inputs,
       scope={"size": ["Bicycle <25"], "powertrain": ["BEV"], "year": [2025]},
   )
   array.loc[dict(parameter="heat pump cost")] = 175.25
   model = TwoWheelerModel(array)
   model.set_all()
   assert model["heat pump cost"].item() == 175.25

A custom input dictionary with explicit ``amount`` and ``loc`` is also
supported. Changing this cost alone does **not** introduce thermal physics,
equipment mass or an inventory exchange; those require separate modelling.

Verification and reproduction
-----------------------------

The audit completed **54 before/after model, inventory and LCIA cases** for
all nine available BEV sizes in 2020, 2025 and 2030. Purchase falls by EUR 300
in each case. All model parameters except heat-pump cost, purchase cost,
annualized purchase and total cost remain identical. Inventory matrices and
LCIA results are identical. The unavailable ``Moped <4kW / BEV`` combination
retains its availability mask; its input default is also zero.

Regression tests check static and seeded sampled input draws, zero costs at
every interpolated year from 2000 through 2050, and completed runs with explicit
array and dictionary overrides. Independent ten-year cash-flow sums verify the
annualized cost difference and show that the charge is applied once without
markup. These checks do not claim that all stochastic model adjustments are
seeded or that complete ownership costs are empirically validated.

The installed package includes :download:`scope, rationale and original records
<../carculator_two_wheeler/data/heat_pump_cost_provenance.json>`. The
:download:`recorded audit <_static/heat_pump_cost_audit.json>` contains the
completed-run results and input hash. Run offline::

   python scripts/validate_heat_pump_costs.py --output /tmp/heat-pump-costs.json
   python -m pytest tests/test_heat_pump_costs.py

Earlier bicycle and small-vehicle audit files remain historical. Their purchase
totals include the old heat-pump charge, and their hashes identify those older
inputs. Their audit scripts isolate their respective glider changes against the
currently installed defaults; rerunning them now also reflects this zero-cost
default and will not reproduce every historical total.
