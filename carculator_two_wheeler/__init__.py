"""

Submodules
==========

.. autosummary::
    :toctree: _autosummary


"""

__all__ = (
    "TwoWheelerInputParameters",
    "fill_xarray_from_input_parameters",
    "modify_xarray_from_custom_parameters",
    "get_standard_driving_cycle",
    "TwoWheelerModel",
    "NoiseEmissionsModel",
    "HotEmissionsModel",
    "InventoryCalculation",
    "BackgroundSystemModel",
    "ExportInventory",
)
__version__ = (0, 0, 1)

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


from .array import (
    fill_xarray_from_input_parameters,
    modify_xarray_from_custom_parameters,
)
from .background_systems import BackgroundSystemModel
from .driving_cycles import get_standard_driving_cycle
from .export import ExportInventory
from .hot_emissions import HotEmissionsModel
from .inventory import InventoryCalculation
from .model import TwoWheelerModel
from .noise_emissions import NoiseEmissionsModel
from .two_wheelers_input_parameters import TwoWheelerInputParameters
