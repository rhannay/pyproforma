"""Table definitions for the Water Utility model."""

from pyproforma import (
    BlankRow,
    HeaderRow,
    ItemRow,
    LabelRow,
    TableDef,
    TagItemsRow,
)

dscr_table = TableDef(
    title="Debt Service Coverage",
    rows=[
        HeaderRow(),
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
    ],
)
