"""

Submodules
==========

.. autosummary::
    :toctree: _autosummary


"""

__all__ = (
    "TwoWheelerInputParameters",
    "fill_xarray_from_input_parameters",
    "TwoWheelerModel",
    "InventoryTwoWheeler",
)
__version__ = (0, 1, 0, "dev0")

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


from carculator_utils.array import fill_xarray_from_input_parameters

from .inventory import InventoryTwoWheeler
from .model import TwoWheelerModel
from .two_wheelers_input_parameters import TwoWheelerInputParameters
