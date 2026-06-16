"""Launch the pyproforma explorer for the Apple three-statement model.

    python examples/three_statement_model/run.py
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import model
from tables import assumptions_table, balance_sheet_table, cash_flow_table, income_statement_table

from pyproforma.explorer import create_app

tables = {
    "Assumptions": assumptions_table,
    "Balance Sheet": balance_sheet_table,
    "Income Statement": income_statement_table,
    "Cash Flow Statement": cash_flow_table,
}

views = {
    "Three Statements": [
        [{"type": "table", "ref": "Assumptions"}],
        [{"type": "table", "ref": "Balance Sheet"}],
        [{"type": "table", "ref": "Income Statement"}],
        [{"type": "table", "ref": "Cash Flow Statement"}],
    ],
}

if __name__ == "__main__":
    app = create_app(model, tables=tables, views=views, home_view="Three Statements")
    app.run(debug=True)
