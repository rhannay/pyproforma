"""
Explorer config loading — build create_app()'s tables/charts/views/home_view
kwargs from a YAML file.

The loader's only job is to produce exactly the Python objects a hand-written
app.py would construct (TableDef instances, InputGroup instances, and
pass-through dicts for stat/chart/table view components) so create_app()
itself needs no awareness that the config came from YAML.
"""

from pathlib import Path

import yaml

from pyproforma.explorer.components import InputGroup
from pyproforma.tables.table_def import TableDef


def load_view_config(path: Path, base_model=None) -> dict:
    """
    Parse a YAML explorer config file into create_app()'s kwargs.

    Args:
        path: Path to a .yaml/.yml file with optional top-level keys
            "tables", "charts", "views", "home_view" — matching create_app()'s
            tables/charts/views/home_view parameters — plus an optional
            "scenarios" key (dict of scenario label -> constructor kwargs).
        base_model: The model already loaded from the target .py file. Only
            required when the config declares "scenarios" — used to derive
            the model class and periods for building each scenario instance.

    Returns:
        dict with keys "tables", "charts", "views", "home_view", ready to pass
        as create_app(model, **load_view_config(path)). If the config declares
        "scenarios", the dict also has a "models" key (dict of label ->
        ProformaModel, including "Base" for base_model itself), ready to pass
        as create_scenario_app(**load_view_config(path, base_model=model)).

    Raises:
        FileNotFoundError: If path doesn't exist.
        ValueError: If path isn't a .yaml/.yml file, a view component
            references a table/chart ref that isn't defined, "scenarios" is
            declared without a base_model, "scenarios" is empty, or
            "scenarios" declares a scenario named "Base".
    """
    if not path.exists():
        raise FileNotFoundError(f"No such file: {path}")
    if path.suffix not in (".yaml", ".yml"):
        raise ValueError(f"Not a YAML file: {path}")

    raw = yaml.safe_load(path.read_text()) or {}

    tables = {label: TableDef.from_dict(entry) for label, entry in raw.get("tables", {}).items()}
    charts = raw.get("charts", {})

    views = {}
    for view_label, row_defs in raw.get("views", {}).items():
        rows = []
        for row_def in row_defs:
            row = []
            for comp in row_def:
                if comp["type"] == "input_group":
                    row.append(
                        InputGroup(
                            names=comp["names"],
                            label=comp.get("label"),
                            orient=comp.get("orient", "vertical"),
                        )
                    )
                else:
                    row.append(comp)
            rows.append(row)
        views[view_label] = rows

    for view_label, rows in views.items():
        for row in rows:
            for comp in row:
                if isinstance(comp, dict) and comp.get("type") in ("chart", "table"):
                    refs = charts if comp["type"] == "chart" else tables
                    if comp["ref"] not in refs:
                        raise ValueError(
                            f"View '{view_label}' references unknown {comp['type']} "
                            f"'{comp['ref']}'."
                        )

    result = {
        "tables": tables,
        "charts": charts,
        "views": views,
        "home_view": raw.get("home_view"),
    }

    scenarios = raw.get("scenarios")
    if scenarios is not None:
        if base_model is None:
            raise ValueError(f"{path} declares 'scenarios' but no base model was provided.")
        if not scenarios:
            raise ValueError("scenarios must declare at least one scenario.")
        if "Base" in scenarios:
            raise ValueError(
                "scenarios must not declare a scenario named 'Base' — that name "
                "is reserved for the model loaded from the .py file."
            )
        model_class = type(base_model)
        periods = base_model.periods
        models = {"Base": base_model}
        for label, kwargs in scenarios.items():
            models[label] = model_class(periods=periods, **kwargs)
        result["models"] = models

    return result
