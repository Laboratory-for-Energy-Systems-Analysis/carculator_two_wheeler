.. _structure:

Structure
=========

.. image:: /_static/img/coarse.png
    :align: center
    :width: 85%
    :alt: Coarse

Modules
-------

Composed of eight modules to build the two-wheeler models:

* Driving cycle module
* Mass module
* Auxiliary energy module
* Motive energy module
* Fuel-related emissions module
* Hot pollutant emissions module
* Non-exhaust emissions module
* Noise emissions module

Additionally, three modules are used to:

* configure energy systems for the background model (background systems module)
* build and solve the life cycle inventory of two-wheelers (inventory module)
* export the life cycle inventory of two-wheelers through ``carculator_utils`` and
  Brightpath (Brightway Excel, SimaPro CSV and foreground-only openLCA JSON-LD;
  see :doc:`inventory_export` for sample selection and background linking)

Driving cycle module
--------------------

.. image:: /_static/img/driving_cycle.png
    :align: center
    :width: 85%
    :alt: Driving Cycle

Mass module
-----------

.. image:: /_static/img/mass_module.png
    :align: center
    :width: 85%
    :alt: Mass Module

Auxiliary energy module
-----------------------

.. image:: /_static/img/aux_energy.png
    :align: center
    :width: 85%
    :alt: Auxiliary Energy
    
Motive energy module
--------------------

.. image:: /_static/img/motive_energy.png
    :align: center
    :width: 85%
    :alt: Motive Energy
