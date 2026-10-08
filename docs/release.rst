Release notes
=============

0.1.1
-----

When upgrading from an earlier version:

* Create a Python 3.12 environment and install the updated package as described
  in :doc:`installation`. This version requires ``carculator_utils>=1.3.6``.
* Recalculate saved scenarios: changes to energy accounting, battery sizing,
  costs and emissions can affect results.
* Select a supported background scenario: ``SSP2-NPi``,
  ``SSP2-PkBudg1000``, ``SSP2-PkBudg650`` or ``static``. Older ``1150`` and
  ``500`` pathway labels are no longer accepted.

The :download:`changelog <../CHANGELOG.md>` lists the changes in each version.
See :doc:`validity` for calibration evidence and the scope of model validation.

Petrol-efficiency defaults and negative small-vehicle glider costs have been
corrected. See :doc:`petrol_efficiency`, :doc:`bicycle_costs` and
:doc:`small_vehicle_costs` for the affected configurations and evidence.

Default BEV purchase costs also drop by EUR 300 after removing an inherited
cabin heat-pump charge. Explicit monetary overrides remain supported; see
:doc:`heat_pump_costs`.

The electric kick-scooter charger now uses a provisional EUR 70 default, reducing
its 2025 purchase result to EUR 279.91; see :doc:`kick_scooter_charger_costs`.
