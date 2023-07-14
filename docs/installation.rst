.. _install:

Installation
============

Python Version
--------------
We recommend using the latest version of Python. ``carculator_two_wheeler`` supports Python 3.7 and above environment.
Because ``carculator_two_wheeler`` is still at an early development stage, we recommend installing it in a separate environment.

Using Conda environment
-----------------------

Create a conda environment:

.. code-block:: bash

    conda create -n <name of the environment> python=3.7

Once your environment created, you should activate it:

.. code-block:: bash

    conda activate <name of the environment>

And install the ``carculator_two_wheeler`` library in your new environment via Conda:

.. code-block:: bash

    conda install -c romainsacchi carculator_two_wheeler

Using Pip
---------

Use the following command to install the ``carculator_two_wheeler`` via ``pip``:

.. code-block:: bash

    pip install carculator_two_wheeler

.. note:: This will install the package and the required dependencies.

How to update this package?
---------------------------

Within the conda environment, type:

.. code-block:: bash

    conda update carculator_two_wheeler

Or from Pypi using pip:

.. code-block:: bash

    pip install --upgrade carculator_two_wheeler