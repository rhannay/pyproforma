"""
PyProforma - A lightweight financial modeling framework.
"""

from .charts.chart_def import ChartDef
from .tables.table_def import TableDef
from .tables.row_types import (
    BlankRow,
    CumulativeChangeRow,
    CumulativePercentChangeRow,
    HeaderRow,
    ItemRow,
    LabelRow,
    LineItemsTotalRow,
    PercentChangeRow,
    TagItemsRow,
    TagTotalRow,
)
from .specs import (
    DebtCalculator,
    DebtInterestLine,
    DebtPrincipalLine,
    FixedLine,
    FormulaLine,
    InputLine,
    LineItem,
    ScalarInputLine,
    ScalarLine,
    create_debt_lines,
)
from .engine import LineItemValue, LineItemValues
from .results import LineItemResult, LineItemSelection, ScalarResult
from .table import Format, NumberFormatSpec
from .compare import ModelComparison
from .proforma_model import ProformaModel
from .tables import Tables
from .results.tags_namespace import TagNamespace

__all__ = [
    "ProformaModel",
    "ChartDef",
    "TableDef",
    "HeaderRow",
    "ItemRow",
    "LabelRow",
    "BlankRow",
    "TagItemsRow",
    "TagTotalRow",
    "LineItemsTotalRow",
    "PercentChangeRow",
    "CumulativeChangeRow",
    "CumulativePercentChangeRow",
    "FixedLine",
    "FormulaLine",
    "InputLine",
    "ScalarLine",
    "ScalarInputLine",
    "ScalarResult",
    "DebtPrincipalLine",
    "DebtInterestLine",
    "DebtCalculator",
    "create_debt_lines",
    "LineItem",
    "LineItemValues",
    "LineItemValue",
    "LineItemResult",
    "LineItemSelection",
    "TagNamespace",
    "Tables",
    "ModelComparison",
    "Format",
    "NumberFormatSpec",
]
