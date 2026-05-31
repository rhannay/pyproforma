"""Launch the pyproforma explorer for the water utility model.

    python examples/water_utility/run.py
"""

import sys
from pathlib import Path

# Project root is two levels up; needed for pyproforma and explorer.
_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_root))

# Ensure the local model.py is importable when run from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import model
from explorer import create_app

if __name__ == "__main__":
    app = create_app(model)
    app.run(debug=True)
