"""Table templates for the Water Utility model."""

from pyproforma.tables.row_types import (
    BlankRow,
    HeaderRow,
    ItemRow,
    LabelRow,
    TagItemsRow,
)

dscr_table = [
    HeaderRow(col_labels=""),
    LabelRow(label="Revenue"),
    TagItemsRow(tag="revenue"),
    ItemRow(name="total_revenue", bold=True, top_border="single"),
    BlankRow(),
    LabelRow(label="O&M Expenses"),
    TagItemsRow(tag="om"),
    ItemRow(name="total_om", bold=True, top_border="single"),
    BlankRow(),
    ItemRow(name="net_revenue", bold=True, top_border="double"),
    BlankRow(),
    LabelRow(label="Debt Service"),
    TagItemsRow(tag="debt_service"),
    ItemRow(name="total_debt_service", bold=True, top_border="single"),
    BlankRow(),
    ItemRow(name="dscr", bold=True),
    ItemRow(name="days_cash_on_hand"),
]
