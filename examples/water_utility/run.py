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
from explorer import create_app
from pyproforma import ChartDef

tables = {
    "Debt Service Coverage": dscr_table,
}

charts = {
    "Revenue": ChartDef(names=["water_sales_revenue", "power_sales"]),
    "O&M Breakdown": ChartDef(
        names=["labor_and_benefits", "power_and_chemicals", "maintenance_and_repairs", "general_and_admin"],
        chart_type="stacked_bar",
    ),
    "Key Ratios": ChartDef(names=["dscr", "days_cash_on_hand"]),
}

views = {
    "Financial Summary": [
        [
            {"type": "stat", "name": "dscr",             "label": "Min DSCR",          "aggregation": "min"},
            {"type": "stat", "name": "ending_cash",       "label": "Ending Cash",       "aggregation": "latest"},
            {"type": "stat", "name": "days_cash_on_hand", "label": "Days Cash on Hand", "aggregation": "latest"},
        ],
        [
            {"type": "chart", "ref": "Revenue"},
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
