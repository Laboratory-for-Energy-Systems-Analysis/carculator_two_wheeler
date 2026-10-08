Release 0.1.1: migration and validation
=======================================

This checkout prepares ``carculator_two_wheeler 0.1.1``; it has not yet been published.
The :download:`changelog <../CHANGELOG.md>` lists package-specific changes and
the :download:`release checklist <../RELEASING.md>` describes artifact verification
and publication order.

Environment and API migration
-----------------------------

Use Python **3.12** (``>=3.12,<3.13``) with NumPy ``>=1.26.4,<2``.
Vehicle packages require the stable ``carculator_utils>=1.3.6`` release.
Core model/LCIA runs need no Brightway project or ecoinvent installation;
``excel`` and ``brightway`` are optional export extras. The Brightway extra
targets ``bw2io<0.9``, ``bw2data<4`` and ``bw2calc<2``.

Use the public vehicle-specific input, model and inventory classes. The array
builder returns ``(mappings, array)``; call ``set_all()`` on a fresh model before
constructing its inventory. See :doc:`installation` and the repository README
for runnable examples using 2025 inputs. Invalid coordinates, fuel shares and
active functional-unit loads now fail explicitly; sizing has a bounded iteration
limit with per-cell diagnostics.

Numerical results and reproducibility
-------------------------------------

Re-run saved scenarios after upgrading. Corrected energy accounting, component
priors, cost annualization, fuel blends, direct CO2 and hot pollutant mapping can
change results from earlier releases. Retain package versions, input overrides,
cycle, load, fuel blend, functional unit and energy meter boundary with results.
Native 2025 parameters and smooth temporal extensions are not evidence that
every configuration has been empirically calibrated. See :doc:`validity`.

``TtW energy`` is kJ/km; for BEVs it is stored-energy depletion. Terminal DC
energy is separately available as ``model.battery_terminal_energy`` and grid
electricity as ``electricity consumption`` in kWh/km. Preserve these boundaries
when comparing measured data. Sampling with ``stochastic(n, seed=...)`` controls
input draws, not every downstream stochastic cost adjustment.

Background scenarios are ``SSP2-NPi``, ``SSP2-PkBudg1000``,
``SSP2-PkBudg650`` and ``static``. Older 1150/500 labels are rejected.
Exports target ecoinvent 3.9 and 3.10; the bundled characterized background
matrices and export target versions are separate choices.

Known limits
------------

* Bicycle and small-vehicle negative glider costs have been corrected with provisional priors. Complete purchase costs, inherited heat-pump/charger charges and currency-year consistency remain unqualified. See :doc:`bicycle_costs` and :doc:`small_vehicle_costs`.
* Manufacturer screening still leaves substantial unmatched consumption residuals; see :doc:`petrol_efficiency`.
* The coupled target-range repair was validated for passenger cars; two-wheeler target-range overrides have not received equivalent qualification.

Verification status
-------------------

On 2026-10-08, the five-package installed-artifact suites passed **497 tests**,
with one existing expected two-wheeler cost failure. Wheel and sdist-built
wheel resource checks, offline core-only model/LCIA runs, strict Twine metadata
checks, README execution and the documented inventory exports passed. All five
Sphinx sites built using the release wheels and their ``docs`` extras.

The :download:`release verification record <_static/release_verification.json>`
contains versions, artifact hashes, test counts and qualifications. Builds were
local on macOS with Python 3.12; hosted CI and conda builds need separate
qualification. Existing documentation warnings are recorded. These checks
exercise packaging and software consistency; they do not establish physical
plausibility or replace the measurement evidence and limitations in :doc:`validity`.

Petrol parameter correction
---------------------------

The five affected petrol classes now use the restored historical efficiency
prior (18.37% in 2025). The default ``Motorcycle 11-35kW`` / ``ICEV-p`` case
returns **1.797 MJ/km**, or **5.646 L/100 km**, instead of 33.0 MJ/km.
See :doc:`petrol_efficiency` for provenance, before/after inventory checks and
manufacturer screening comparisons. Several unmatched consumption residuals
remain large; this correction is not a claim of completed empirical calibration.
Publication remains pending maintainer review of the remaining known issues.

The subsequent :doc:`bicycle_costs` correction removes the bicycle cost expected
failure. The :doc:`small_vehicle_costs` correction extends the repair to kick-scooters,
mopeds and small scooters. The older verification record above describes the
pre-correction artifacts.
