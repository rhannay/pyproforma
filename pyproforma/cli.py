"""
pyproforma CLI — launch the explorer app for a model file.

Usage:
    pyproforma path/to/model.py
"""

import argparse
import importlib.util
import sys
from pathlib import Path

from pyproforma import ProformaModel


def _find_model(module, path: Path) -> ProformaModel:
    """Find the single ProformaModel instance defined at module level."""
    matches = [
        (name, value) for name, value in vars(module).items() if isinstance(value, ProformaModel)
    ]
    if not matches:
        raise ValueError(f"No ProformaModel instance found in {path}")
    if len(matches) > 1:
        names = ", ".join(name for name, _ in matches)
        raise ValueError(
            f"Multiple ProformaModel instances found in {path}: {names}. Expected exactly one."
        )
    return matches[0][1]


def load_model_from_file(path: Path) -> ProformaModel:
    """Import a .py file and return the single ProformaModel instance in it."""
    if not path.exists():
        raise FileNotFoundError(f"No such file: {path}")
    if path.suffix != ".py":
        raise ValueError(f"Not a Python file: {path}")

    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    spec = importlib.util.spec_from_file_location(f"_pyproforma_cli_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return _find_model(module, path)


def build_app(path: Path):
    """Load the model at path and return a Flask app for the explorer."""
    try:
        from pyproforma.explorer import create_app
    except ImportError as e:
        raise ImportError(
            "Explorer support requires the 'explorer' extra: pip install pyproforma[explorer]"
        ) from e

    model = load_model_from_file(path)
    return create_app(model)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pyproforma", description="Launch the pyproforma explorer for a model file."
    )
    parser.add_argument("model_file", help="Path to a .py file containing a ProformaModel instance")
    args = parser.parse_args(argv)

    try:
        app = build_app(Path(args.model_file))
    except (FileNotFoundError, ValueError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    app.run(debug=True)


if __name__ == "__main__":
    main()
