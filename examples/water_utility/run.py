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

charts = {
    "Revenue": {
        "names": ["water_sales_revenue", "power_sales"],
        "chart_type": "line",
    },
    "O&M Breakdown": {
        "names": ["labor_and_benefits", "power_and_chemicals", "maintenance_and_repairs", "general_and_admin"],
        "chart_type": "stacked_bar",
    },
    "Key Ratios": {
        "names": ["dscr", "days_cash_on_hand"],
        "chart_type": "line",
    },
}

if __name__ == "__main__":
    app = create_app(model, tables={"Debt Service Coverage": dscr_table}, charts=charts)
    app.run(debug=True)
