"""
Tables namespace for PyProforma v2 API.

This module provides table creation functionality for v2 models, 
reusing the Table class from the main table module.
"""

from .row_types import (
    BaseRow,
    BlankRow,
    CumulativeChangeRow,
    CumulativePercentChangeRow,
    ItemRow,
    LabelRow,
    LineItemsTotalRow,
    PercentChangeRow,
    dict_to_row_config,
)
from .tables import Tables

__all__ = [
    "Tables",
    "BaseRow",
    "ItemRow",
    "LabelRow",
    "BlankRow",
    "PercentChangeRow",
    "CumulativeChangeRow",
    "CumulativePercentChangeRow",
    "LineItemsTotalRow",
    "dict_to_row_config",
]
