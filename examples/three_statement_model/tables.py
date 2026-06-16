"""
Table definitions for the Apple three-statement model.

Build tables via:
    from model import model
    from tables import income_statement_table, balance_sheet_table, cash_flow_table

    model.tables.build(income_statement_table).show()
    model.tables.build(balance_sheet_table).show()
    model.tables.build(cash_flow_table).show()

FY2022–FY2024 = Actuals (approximate, from Apple 10-K filings)
FY2025–FY2029 = Projected
All figures in millions of USD.
"""

from pyproforma import (
    BlankRow,
    HeaderRow,
    ItemRow,
    LabelRow,
    ScalarRow,
    TableDef,
)

income_statement_table = TableDef(
    title="Apple Inc. — Income Statement ($M) | FY2022–2024 Actual | FY2025–2029 Projected",
    rows=[
        HeaderRow(),
        ItemRow(name="revenue"),
        ItemRow(name="cogs", label="  Cost of Sales"),
        ItemRow(name="gross_profit", bold=True, top_border="single"),
        ItemRow(name="gross_margin"),
        BlankRow(),
        LabelRow(label="Operating Expenses"),
        ItemRow(name="rd_expense", label="  Research & Development"),
        ItemRow(name="sga_expense", label="  Selling, General & Admin"),
        BlankRow(),
        ItemRow(name="ebit", bold=True, top_border="single"),
        ItemRow(name="ebit_margin"),
        BlankRow(),
        ItemRow(name="other_income_net", label="  Other Income/(Expense), Net"),
        ItemRow(name="ebt"),
        ItemRow(name="income_tax", label="  Income Tax Expense"),
        ItemRow(name="net_income", bold=True, top_border="double"),
        ItemRow(name="net_margin"),
    ],
)

balance_sheet_table = TableDef(
    title="Apple Inc. — Balance Sheet ($M) | FY2022–2024 Actual | FY2025–2029 Projected",
    rows=[
        HeaderRow(),
        LabelRow(label="Assets"),
        ItemRow(name="cash_balance", label="  Cash & Equivalents"),
        ItemRow(name="ar_balance", label="  Accounts Receivable"),
        ItemRow(name="inventory_balance", label="  Inventories"),
        ItemRow(name="ppe_net", label="  PP&E, Net"),
        ItemRow(name="other_assets", label="  Other Assets"),
        ItemRow(name="total_assets", bold=True, top_border="double"),
        BlankRow(),
        LabelRow(label="Liabilities"),
        ItemRow(name="ap_balance", label="  Accounts Payable"),
        ItemRow(name="lt_debt", label="  Long-Term Debt"),
        ItemRow(name="other_liabilities", label="  Other Liabilities"),
        ItemRow(name="total_liabilities", bold=True, top_border="single"),
        BlankRow(),
        LabelRow(label="Stockholders' Equity"),
        ItemRow(name="total_equity", bold=True, top_border="single"),
    ],
)

cash_flow_table = TableDef(
    title="Apple Inc. — Cash Flow Statement ($M) | FY2022–2024 Actual | FY2025–2029 Projected",
    rows=[
        HeaderRow(),
        LabelRow(label="Operating Activities"),
        ItemRow(name="net_income", label="  Net Income"),
        ItemRow(name="depreciation_amortization", label="  Depreciation & Amortization"),
        ItemRow(name="wc_changes", label="  Changes in Working Capital"),
        ItemRow(name="other_cfo_adj", label="  Other Adjustments"),
        ItemRow(name="cfo", bold=True, top_border="single"),
        BlankRow(),
        LabelRow(label="Investing Activities"),
        ItemRow(name="capital_expenditures", label="  Capital Expenditures"),
        ItemRow(name="investing_other", label="  Net Investment Activity"),
        ItemRow(name="cfi", bold=True, top_border="single"),
        BlankRow(),
        LabelRow(label="Financing Activities"),
        ItemRow(name="debt_change", label="  Net Debt Issuance/(Repayment)"),
        ItemRow(name="dividends_paid", label="  Dividends Paid"),
        ItemRow(name="share_repurchases", label="  Share Repurchases"),
        ItemRow(name="other_cff", label="  Other Financing"),
        ItemRow(name="cff", bold=True, top_border="single"),
        BlankRow(),
        ItemRow(name="net_cash_change", bold=True, top_border="double"),
        ItemRow(name="beginning_cash"),
        ItemRow(name="cash_balance", label="Ending Cash & Equivalents", bold=True),
    ],
)

assumptions_table = TableDef(
    title="Apple Inc. — Projection Assumptions (FY2025–2029)",
    rows=[
        HeaderRow(),
        LabelRow(label="Income Statement"),
        ScalarRow(name="revenue_growth_rate"),
        ScalarRow(name="gross_margin_pct"),
        ScalarRow(name="rd_pct"),
        ScalarRow(name="sga_pct"),
        ScalarRow(name="other_income_proj"),
        ScalarRow(name="effective_tax_rate"),
        BlankRow(),
        LabelRow(label="Cash Flow"),
        ScalarRow(name="da_pct"),
        ScalarRow(name="capex_pct"),
        BlankRow(),
        LabelRow(label="Working Capital (Days)"),
        ScalarRow(name="ar_days"),
        ScalarRow(name="inventory_days"),
        ScalarRow(name="ap_days"),
        BlankRow(),
        LabelRow(label="Financing"),
        ScalarRow(name="annual_dividends"),
        ScalarRow(name="annual_buybacks"),
        ScalarRow(name="annual_debt_repayment"),
    ],
)
