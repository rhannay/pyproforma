"""Run this file to launch the pyproforma explorer with an example model.

    python flask_pyproforma/example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyproforma import Assumption, FixedLine, FormulaLine, ProformaModel
from flask_pyproforma import create_app


class IncomeStatement(ProformaModel):
    tax_rate = Assumption(value=0.21, label="Tax Rate")
    cogs_rate = Assumption(value=0.55, label="COGS Rate")

    revenue = FixedLine(
        values={2024: 1_000_000, 2025: 1_100_000, 2026: 1_210_000, 2027: 1_331_000},
        label="Revenue",
        tags=["operating"],
    )
    cogs = FormulaLine(
        formula=lambda li, t: li.revenue[t] * li.cogs_rate,
        label="Cost of Goods Sold",
        tags=["operating"],
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.cogs[t],
        label="Gross Profit",
    )
    operating_expenses = FixedLine(
        values={2024: 150_000, 2025: 160_000, 2026: 172_000, 2027: 185_000},
        label="Operating Expenses",
        tags=["operating"],
    )
    ebit = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] - li.operating_expenses[t],
        label="EBIT",
    )
    tax_expense = FormulaLine(
        formula=lambda li, t: li.ebit[t] * li.tax_rate,
        label="Tax Expense",
    )
    net_income = FormulaLine(
        formula=lambda li, t: li.ebit[t] - li.tax_expense[t],
        label="Net Income",
    )


if __name__ == "__main__":
    model = IncomeStatement(periods=[2024, 2025, 2026, 2027])
    app = create_app(model)
    app.run(debug=True)
