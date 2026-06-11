"""
PyProforma - A lightweight financial modeling framework.
"""

from .charts.chart_def import ChartDef
from .compare import ModelComparison
from .engine import LineItemValue, LineItemValues
from .proforma_model import ProformaModel
from .results import LineItemResult, LineItemSelection, ScalarResult
from .results.tags_namespace import TagNamespace
from .specs import (
    DebtCalculator,
    DebtConfig,
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
from .table import Format, NumberFormatSpec
from .tables import Tables
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
from .tables.table_def import TableDef

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
    "DebtConfig",
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
