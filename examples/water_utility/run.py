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

if __name__ == "__main__":
    app = create_app(model, tables={"Debt Service Coverage": dscr_table})
    app.run(debug=True)
