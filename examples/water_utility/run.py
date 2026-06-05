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
from pyproforma.explorer import create_app
from pyproforma.explorer.components import StatCard
from pyproforma import ChartDef

tables = {
    "Debt Service Coverage": dscr_table,
}

charts = {
    "Revenue": ChartDef(names=["water_sales_revenue", "power_sales"]),
    "Revenue & O&M": ChartDef(names=["total_revenue", "total_om"]),
    "O&M Breakdown": ChartDef(
        names=["labor_and_benefits", "power_and_chemicals", "maintenance_and_repairs", "general_and_admin"],
        chart_type="stacked_bar",
    ),
    "Key Ratios": ChartDef(names=["dscr", "days_cash_on_hand"]),
}

views = {
    "Financial Summary": [
        [
            StatCard("dscr",             "Min DSCR",          aggregation="min"),
            StatCard("ending_cash",      "Ending Cash"),
            StatCard("days_cash_on_hand","Days Cash on Hand"),
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
    app = create_app(model, tables=tables, charts=charts, views=views)
    app.run(debug=True)
