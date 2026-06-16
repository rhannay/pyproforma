"""
Apple Inc. — Three-Statement Financial Model
FY2022–FY2024: Historical actuals (approximate, sourced from Apple 10-K filings)
FY2025–FY2029: Projections driven by revenue growth and margin assumptions
All figures in millions of USD.

The three statements are linked:
  • Net income from the Income Statement flows into the Cash Flow Statement.
  • The CFS computes the net change in cash, which rolls to the Balance Sheet.
  • Balance Sheet working capital items (AR, inventory, AP) drive CFS WC changes.
  • PP&E rolls forward via capex and D&A; long-term debt rolls via repayments.
  • Equity is the residual (total assets − total liabilities), so the BS always balances.
"""

from pyproforma import (
    Format,
    FormulaLine,
    ProformaModel,
    ScalarLine,
)

PERIODS = list(range(2022, 2030))  # FY2022–FY2029


class AppleModel(ProformaModel):
    default_periods = PERIODS
    period_label = "Fiscal Year"

    # ════════════════════════════════════════════════════════════════════════
    # PROJECTION ASSUMPTIONS (scalars — no [t], accessed as li.name)
    # ════════════════════════════════════════════════════════════════════════

    revenue_growth_rate = ScalarLine(
        value=0.07,
        label="Revenue Growth Rate (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    gross_margin_pct = ScalarLine(
        value=0.465,
        label="Gross Margin % (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    rd_pct = ScalarLine(
        value=0.080,
        label="R&D % of Revenue (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    sga_pct = ScalarLine(
        value=0.067,
        label="SG&A % of Revenue (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    other_income_proj = ScalarLine(
        value=1_500,
        label="Other Income, Net (Proj., $M)",
        value_format=Format.NO_DECIMALS,
    )
    effective_tax_rate = ScalarLine(
        value=0.22,
        label="Effective Tax Rate (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    da_pct = ScalarLine(
        value=0.029,
        label="D&A % of Revenue (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    capex_pct = ScalarLine(
        value=0.025,
        label="Capex % of Revenue (Proj.)",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    ar_days = ScalarLine(
        value=31,
        label="AR Days (Proj.)",
        value_format=Format.NO_DECIMALS,
    )
    inventory_days = ScalarLine(
        value=7,
        label="Inventory Days (Proj.)",
        value_format=Format.NO_DECIMALS,
    )
    ap_days = ScalarLine(
        value=105,
        label="AP Days (Proj.)",
        value_format=Format.NO_DECIMALS,
    )
    annual_dividends = ScalarLine(
        value=15_500,
        label="Dividends Paid (Proj., $M)",
        value_format=Format.NO_DECIMALS,
    )
    annual_buybacks = ScalarLine(
        value=90_000,
        label="Share Repurchases (Proj., $M)",
        value_format=Format.NO_DECIMALS,
    )
    annual_debt_repayment = ScalarLine(
        value=9_000,
        label="Net Debt Repayment (Proj., $M)",
        value_format=Format.NO_DECIMALS,
    )

    # ════════════════════════════════════════════════════════════════════════
    # INCOME STATEMENT
    # Historical periods use seed values (values={}) from Apple 10-K filings.
    # Projection periods evaluate the formula lambda.
    # ════════════════════════════════════════════════════════════════════════

    revenue = FormulaLine(
        formula=lambda li, t: li.revenue[t - 1] * (1 + li.revenue_growth_rate),
        values={2022: 394_328, 2023: 383_285, 2024: 391_035},
        label="Net Revenue",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * (1 - li.gross_margin_pct),
        values={2022: 223_546, 2023: 214_137, 2024: 210_352},
        label="Cost of Sales",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    gross_margin = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] / li.revenue[t],
        label="Gross Margin %",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    rd_expense = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.rd_pct,
        values={2022: 26_251, 2023: 29_915, 2024: 31_370},
        label="Research & Development",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    sga_expense = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.sga_pct,
        values={2022: 25_094, 2023: 24_932, 2024: 26_097},
        label="Selling, General & Admin",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    ebit = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] - li.rd_expense[t] - li.sga_expense[t],
        label="Operating Income (EBIT)",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    ebit_margin = FormulaLine(
        formula=lambda li, t: li.ebit[t] / li.revenue[t],
        label="EBIT Margin %",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    other_income_net = FormulaLine(
        formula=lambda li, t: li.other_income_proj,
        values={2022: 796, 2023: 1_712, 2024: 1_190},
        label="Other Income/(Expense), Net",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    ebt = FormulaLine(
        formula=lambda li, t: li.ebit[t] + li.other_income_net[t],
        label="Income Before Taxes",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    income_tax = FormulaLine(
        formula=lambda li, t: li.ebt[t] * li.effective_tax_rate,
        values={2022: 20_430, 2023: 19_018, 2024: 30_670},
        label="Income Tax Expense",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.ebt[t] - li.income_tax[t],
        label="Net Income",
        value_format=Format.NO_DECIMALS,
        tags=["income_statement"],
    )
    net_margin = FormulaLine(
        formula=lambda li, t: li.net_income[t] / li.revenue[t],
        label="Net Margin %",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )

    # ════════════════════════════════════════════════════════════════════════
    # CASH FLOW STATEMENT
    # Operating, investing, and financing sections. The net change in cash
    # feeds directly into cash_balance on the Balance Sheet (for projections).
    # ════════════════════════════════════════════════════════════════════════

    depreciation_amortization = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.da_pct,
        values={2022: 11_104, 2023: 11_519, 2024: 11_445},
        label="Depreciation & Amortization",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    # WC changes for projections are derived from BS item changes.
    # For actuals, hardcoded totals from the reported cash flow statement.
    wc_changes = FormulaLine(
        formula=lambda li, t: (
            -(li.ar_balance[t] - li.ar_balance[t - 1])
            - (li.inventory_balance[t] - li.inventory_balance[t - 1])
            + (li.ap_balance[t] - li.ap_balance[t - 1])
        ),
        values={2022: 8_726, 2023: 2_827, 2024: 10_273},
        label="Changes in Working Capital",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    other_cfo_adj = FormulaLine(
        formula=lambda li, t: 2_800,
        values={2022: 2_518, 2023: 2_918, 2024: 2_800},
        label="Other Operating Adjustments",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    cfo = FormulaLine(
        formula=lambda li, t: (
            li.net_income[t]
            + li.depreciation_amortization[t]
            + li.wc_changes[t]
            + li.other_cfo_adj[t]
        ),
        label="Cash from Operations",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    # Stored as a negative value (cash outflow); absolute capex = -capital_expenditures.
    capital_expenditures = FormulaLine(
        formula=lambda li, t: -li.revenue[t] * li.capex_pct,
        values={2022: -10_708, 2023: -10_959, 2024: -9_447},
        label="Capital Expenditures",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    investing_other = FormulaLine(
        formula=lambda li, t: 0,
        values={2022: -11_646, 2023: 7_288, 2024: 12_382},
        label="Net Investment Activity",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    cfi = FormulaLine(
        formula=lambda li, t: li.capital_expenditures[t] + li.investing_other[t],
        label="Cash from Investing",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    debt_change = FormulaLine(
        formula=lambda li, t: -li.annual_debt_repayment,
        values={2022: -9_543, 2023: -11_151, 2024: -5_998},
        label="Net Debt Issuance/(Repayment)",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    dividends_paid = FormulaLine(
        formula=lambda li, t: -li.annual_dividends,
        values={2022: -14_841, 2023: -15_025, 2024: -15_234},
        label="Dividends Paid",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    share_repurchases = FormulaLine(
        formula=lambda li, t: -li.annual_buybacks,
        values={2022: -89_402, 2023: -77_550, 2024: -95_000},
        label="Share Repurchases",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    other_cff = FormulaLine(
        formula=lambda li, t: -3_000,
        values={2022: 3_037, 2023: -4_762, 2024: -5_746},
        label="Other Financing Activities",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    cff = FormulaLine(
        formula=lambda li, t: (
            li.debt_change[t]
            + li.dividends_paid[t]
            + li.share_repurchases[t]
            + li.other_cff[t]
        ),
        label="Cash from Financing",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    net_cash_change = FormulaLine(
        formula=lambda li, t: li.cfo[t] + li.cfi[t] + li.cff[t],
        label="Net Change in Cash",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )
    # Actuals are hardcoded from Apple 10-K (each year's opening = prior year's close).
    # For projection years the formula carries forward the prior ending balance.
    # Note: the projected net_cash_change will reconcile perfectly; for actuals the
    # CFS components are approximate so beginning + net_change may differ slightly
    # from ending_cash (which is the authoritative hardcoded BS value).
    beginning_cash = FormulaLine(
        formula=lambda li, t: li.cash_balance[t - 1],
        values={2022: 34_940, 2023: 23_646, 2024: 29_965},
        label="Beginning Cash & Equivalents",
        value_format=Format.NO_DECIMALS,
        tags=["cash_flow"],
    )

    # ════════════════════════════════════════════════════════════════════════
    # BALANCE SHEET
    # For projections, each BS item rolls forward from its prior-year seed.
    # Equity is the residual (total assets − total liabilities), so the BS
    # always balances by construction.
    # ════════════════════════════════════════════════════════════════════════

    # ── Current Assets ────────────────────────────────────────────────────
    # Cash rolls forward via the CFS net change for projection years.
    cash_balance = FormulaLine(
        formula=lambda li, t: li.cash_balance[t - 1] + li.net_cash_change[t],
        values={2022: 23_646, 2023: 29_965, 2024: 29_943},
        label="Cash & Equivalents",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_assets"],
    )
    ar_balance = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.ar_days / 365,
        values={2022: 28_184, 2023: 29_508, 2024: 33_410},
        label="Accounts Receivable",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_assets"],
    )
    inventory_balance = FormulaLine(
        formula=lambda li, t: li.cogs[t] * li.inventory_days / 365,
        values={2022: 4_946, 2023: 6_331, 2024: 7_286},
        label="Inventories",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_assets"],
    )

    # ── Non-Current Assets ────────────────────────────────────────────────
    # PP&E rolls: prior + capex spent (−capex, since capex is negative) − D&A.
    ppe_net = FormulaLine(
        formula=lambda li, t: (
            li.ppe_net[t - 1]
            - li.capital_expenditures[t]   # capex is negative, so this adds
            - li.depreciation_amortization[t]
        ),
        values={2022: 42_117, 2023: 43_715, 2024: 45_680},
        label="PP&E, Net",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_assets"],
    )
    # Bucket for LT investments, goodwill/intangibles, deferred taxes, and other.
    # Grows at 2% annually in projections as a simplifying assumption.
    other_assets = FormulaLine(
        formula=lambda li, t: li.other_assets[t - 1] * 1.02,
        values={2022: 253_862, 2023: 243_064, 2024: 248_661},
        label="Other Assets (Investments & Other)",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_assets"],
    )
    total_assets = FormulaLine(
        formula=lambda li, t: (
            li.cash_balance[t]
            + li.ar_balance[t]
            + li.inventory_balance[t]
            + li.ppe_net[t]
            + li.other_assets[t]
        ),
        label="Total Assets",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet"],
    )

    # ── Liabilities ───────────────────────────────────────────────────────
    ap_balance = FormulaLine(
        formula=lambda li, t: li.cogs[t] * li.ap_days / 365,
        values={2022: 64_115, 2023: 62_611, 2024: 68_960},
        label="Accounts Payable",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_liabilities"],
    )
    lt_debt = FormulaLine(
        formula=lambda li, t: li.lt_debt[t - 1] - li.annual_debt_repayment,
        values={2022: 98_959, 2023: 95_281, 2024: 86_198},
        label="Long-Term Debt",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_liabilities"],
    )
    # Catch-all for accrued expenses, deferred revenue, current debt maturities,
    # and other liabilities not modeled individually. Grows 3% annually in projections.
    other_liabilities = FormulaLine(
        formula=lambda li, t: li.other_liabilities[t - 1] * 1.03,
        values={2022: 138_009, 2023: 132_645, 2024: 152_872},
        label="Other Liabilities",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet_liabilities"],
    )
    total_liabilities = FormulaLine(
        formula=lambda li, t: (
            li.ap_balance[t] + li.lt_debt[t] + li.other_liabilities[t]
        ),
        label="Total Liabilities",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet"],
    )
    # Equity is the residual. In actuals this equals reported equity.
    # In projections it implicitly absorbs net income, buybacks, dividends,
    # and any rounding in the other_assets / other_liabilities approximations.
    total_equity = FormulaLine(
        formula=lambda li, t: li.total_assets[t] - li.total_liabilities[t],
        label="Total Stockholders' Equity",
        value_format=Format.NO_DECIMALS,
        tags=["balance_sheet"],
    )


model = AppleModel()
