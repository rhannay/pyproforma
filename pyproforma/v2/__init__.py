"""
PyProforma v2 - Simplified modeling framework

Version 2 provides a cleaner, Pydantic-inspired API for building financial models.
"""

from .assumption import Assumption
from .assumption_result import AssumptionResult
from .assumption_values import AssumptionValues
from .line_items import (
    DebtCalculator,
    DebtInterestLine,
    DebtPrincipalLine,
    FixedLine,
    FormulaLine,
    LineItem,
    LineItemResult,
    LineItemSelection,
    LineItemValue,
    LineItemValues,
    create_debt_lines,
)
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
