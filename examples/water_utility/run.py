"""Launch the pyproforma explorer for the water utility model.

    python examples/water_utility/run.py
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import model
from tables import dscr_table

from pyproforma import ChartDef, Format
from pyproforma.explorer import create_app
from pyproforma.explorer.components import InputGroup, StatCard

tables = {
    "Debt Service Coverage": dscr_table,
}

charts = {
    "Revenue": ChartDef(names=["water_sales_revenue", "power_sales"]),
    "Revenue & O&M": ChartDef(names=["total_revenue", "total_om"]),
    "O&M Breakdown": ChartDef(
        names=["labor_and_benefits", "power_and_chemicals", "maintenance_and_repairs", "general_and_admin"],  # noqa: E501
        chart_type="stacked_bar",
    ),
    "Key Ratios": ChartDef(names=["dscr", "days_cash_on_hand"]),
    "DSCR": ChartDef(names=["dscr"]),
}

views = {
    "Update Rates": [
        [
            InputGroup(names=["rate_increase"], label="Annual Rate Increases"),
            {"type": "chart", "ref": "DSCR"},
        ],
    ],
    "Update Assumptions": [
        [
            InputGroup(
                names=["inflation_rate", "new_bond_rate", "rate_increase"],
                label="Scenario Inputs",
                orient="horizontal",
            ),
        ],
        [
            {"type": "chart", "ref": "Revenue & O&M"},
            {"type": "chart", "ref": "Key Ratios"},
        ],
    ],
    "Financial Summary": [
        [
            StatCard("dscr",             "Min DSCR",          aggregation="min"),
            StatCard("ending_cash",      "Ending Cash"),
            StatCard("days_cash_on_hand","Days Cash on Hand"),
            StatCard(
                "capital_spending", "Total Capex",
                aggregation="sum", value_format=Format.CURRENCY_MILLIONS_M,
            ),
        ],
        [
            {"type": "chart", "ref": "Revenue & O&M"},
            {"type": "chart", "ref": "O&M Breakdown"},
        ],
        [
            {"type": "table", "ref": "Debt Service Coverage"},
        ],
    ],
}

if __name__ == "__main__":
    app = create_app(
        model, tables=tables, charts=charts, views=views, home_view="Financial Summary"
    )
    app.run(debug=True)
