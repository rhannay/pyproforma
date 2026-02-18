"""
PyProforma v2 - Simplified modeling framework

Version 2 provides a cleaner, Pydantic-inspired API for building financial models.
"""

from .assumption import Assumption
from .assumption_result import AssumptionResult
from .assumption_values import AssumptionValues
from .debt_line import (
    DebtCalculator,
    DebtInterestLine,
    DebtPrincipalLine,
    create_debt_lines,
)
from .fixed_line import FixedLine
from .formula_line import FormulaLine
from .line_item import LineItem
from .line_item_result import LineItemResult
from .line_item_selection import LineItemSelection
from .line_item_values import LineItemValue, LineItemValues
from .proforma_model import ProformaModel
from .tables import Tables
from .tags_namespace import ModelTagNamespace

__all__ = [
    "ProformaModel",
    "FixedLine",
    "FormulaLine",
    "DebtPrincipalLine",
    "DebtInterestLine",
    "DebtCalculator",
    "create_debt_lines",
    "Assumption",
    "AssumptionResult",
    "LineItem",
    "AssumptionValues",
    "LineItemValues",
    "LineItemValue",
    "LineItemResult",
    "LineItemSelection",
    "ModelTagNamespace",
    "Tables",
]
