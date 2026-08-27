"""pyproforma explorer for the coffee shop model.

Run directly:
    python examples/coffee_shop/app.py

Or with the Flask CLI (from this directory):
    flask run
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import model

from pyproforma.explorer import create_app

app = create_app(model)

if __name__ == "__main__":
    app.run(debug=True)
