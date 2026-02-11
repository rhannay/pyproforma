"""
PyProforma v2 - Simplified modeling framework

Version 2 provides a cleaner, Pydantic-inspired API for building financial models.
"""

from .assumption import Assumption
from .fixed_line import FixedLine
from .formula_line import FormulaLine
from .proforma_model import ProformaModel

__all__ = ["ProformaModel", "FixedLine", "FormulaLine", "Assumption"]
