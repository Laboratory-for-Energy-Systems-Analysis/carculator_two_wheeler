Battery replacement accounting
==============================

Two-wheelers do **not** require a replacement battery merely because they are
electric. The 2026-10-08 correction removes the former minimum of one replacement.
The initial battery is still included in purchase cost, production and disposal.
This is a replacement-policy correction, not a change to battery sizing,
chemistry, cycle-life inputs or energy consumption.

Current calculation
-------------------

For a vehicle with a charger, the replacement factor is:

.. math::

   r = \min\left(3,\max\left(0,
       \frac{D\,E}{3600\,C\,N}-1\right)\right)

Here ``D`` is lifetime distance in km, ``E`` is stored-energy depletion in kJ/km
(``TtW energy``), ``C`` is nominal capacity in kWh (``electric energy stored``),
and ``N`` is ``battery cycle life``. ``D * E / (3600 * C)`` is lifetime
throughput expressed as equivalent full cycles of nominal capacity. The
calculation does not divide by usable capacity or add a separate DoD correction.
Depth of discharge still affects range and range-constrained battery sizing.

The first pack supplies the first battery life. A requirement of one battery
life or less gives zero replacements; 1.5 lives gives 0.5 replacements; two
lives gives one replacement. The existing upper bound of three replacements
is retained. These are **fractional allocations**, not rounded counts of actual
replacement events. The old docstring's claim that replacements were rounded
up was incorrect. Vehicles without a charger receive no energy-battery
replacement factor through this calculation.

No separate calendar-ageing or minimum-replacement rule is imposed on
two-wheelers. Zero here means the configured cycling calculation requires no
replacement; it does not establish measured battery survival over the vehicle's
calendar lifetime. Cycle-life priors, fractional allocation and the cap remain
modelling assumptions. A measured cycle life at a particular DoD needs a
compatible throughput interpretation before being used as ``N``.

The bus model deliberately retains its own minimum of one replacement over
service life. That assumption is specific to buses and is documented in
``carculator_bus``; it is not inherited by two-wheelers.

Costs and inventories
---------------------

Battery production and end-of-life quantities both use ``pack mass * (1 + r)``.
The replacement purchase cost uses nominal capacity, battery unit cost and
``r``, with the existing markup. The cost model discounts that amount at the
midpoint of vehicle life before annualizing it. That convention is retained;
it is not a schedule of individual replacement dates.

Completed default 2025 cases illustrate the change:

.. list-table:: Battery supply and total cost
   :header-rows: 1

   * - BEV size
     - Supply before, kg
     - Supply after, kg
     - Total before, EUR/vkm
     - Total after, EUR/vkm
   * - Kick-scooter
     - 3.2
     - 1.6
     - 0.20450
     - 0.17331
   * - Bicycle <25
     - 6.6
     - 3.3
     - 0.07678
     - 0.07110
   * - Scooter <4kW
     - 32.0
     - 16.0
     - 0.16380
     - 0.14207

All nine available BEV sizes in 2020, 2025 and 2030 have zero calculated
replacements with the current default inputs. In 27 paired before/after cases,
all physical outputs and purchase costs remain identical. Only replacement
counts and associated ownership costs change in the model array. In the
inventory matrices, only battery supply and end-of-life exchanges change;
LCIA results remain finite and reflect those changed exchanges. These are
accounting checks, not empirical durability or ownership-cost validation.

``tests/test_battery_replacements.py`` also completes model/inventory runs for
zero, fractional, one, two and capped replacement factors across labelled
samples and two DoD settings. It checks supply/disposal mass, charging inputs,
markup and independent discounted repayment sums. Human and petrol scopes
retain zero energy-battery replacements. Run::

   python -m pytest tests/test_battery_replacements.py

Earlier cost-audit tables record the assumptions in force when those repairs
were made; their total costs predate this replacement correction.
