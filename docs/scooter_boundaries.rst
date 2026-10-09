Scooter inventory boundaries
============================

Disposal
--------

The extra electric-scooter dismantling exchange has been removed from petrol
scooters and motorcycles. Their ``motor scooter production`` proxy (RER, unit,
``motor scooter, 50 cubic cm engine``) already includes disposal. This is stated
in `Sacchi and Bauer (2023), printed pages 39 and 44
<https://zenodo.org/records/7788737>`_ and was verified against the exact supplier
metadata in the existing ``ecoinvent-3.12-cutoff`` Brightway project/database
(activity code ``4b36f9b7f41eb11f708e018c368878a1``).

Electric scooters and motorcycles retain separate dismantling. The exact
``manual dismantling of used electric scooter`` supplier (GLO, unit, reference
product ``manual dismantling of electric scooter``, code
``0a6b71d475adfe9ef0d1643d70100157``) documents treatment per **kg**, despite its
legacy ``unit`` label. Its coefficient remains curb mass in kg. The facility
service does not itself represent every downstream material-treatment process.
The source report, printed page 42, distinguishes the electric production and
disposal boundaries.

Completed inventory and LCIA regressions cover all petrol classes, electric
controls, 2025/2030, different samples and reordered scopes. Brightway and SimaPro
export checks require absent petrol dismantling exchanges and retained electric
amounts. Vehicle energy and mass calculations are unchanged. These checks do not
constitute a fresh validation of every downstream waste-treatment inventory.
