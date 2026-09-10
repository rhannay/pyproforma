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


def build_app(path: Path, config_path: Path | None = None):
    """Load the model at path and return a Flask app for the explorer.

    A relative config_path is resolved against path's directory (not the
    current working directory), so --config can be a bare filename when the
    config lives next to the model file.
    """
    try:
        from pyproforma.explorer import create_app, create_scenario_app
    except ImportError as e:
        raise ImportError(
            "Explorer support requires the 'explorer' extra: pip install pyproforma[explorer]"
        ) from e

    model = load_model_from_file(path)

    if config_path is None:
        return create_app(model)

    if not config_path.is_absolute():
        config_path = path.parent / config_path

    from pyproforma.explorer.config import load_view_config

    config = load_view_config(config_path, base_model=model)
    if "models" in config:
        return create_scenario_app(**config)
    return create_app(model, **config)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pyproforma", description="Launch the pyproforma explorer for a model file."
    )
    parser.add_argument("model_file", help="Path to a .py file containing a ProformaModel instance")
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a YAML file configuring tables/charts/views. A relative "
        "path is resolved against the model file's directory.",
    )
    args = parser.parse_args(argv)

    try:
        config_path = Path(args.config) if args.config else None
        app = build_app(Path(args.model_file), config_path=config_path)
    except (FileNotFoundError, ValueError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    app.run(debug=True)


if __name__ == "__main__":
    main()
