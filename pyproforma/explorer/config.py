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

from pyproforma.explorer.compare_defs import CompareChartDef, CompareTableDef
from pyproforma.explorer.components import InputGroup
from pyproforma.tables.table_def import TableDef


def load_view_config(path: Path, base_model=None) -> dict:
    """
    Parse a YAML explorer config file into create_app()'s kwargs.

    Args:
        path: Path to a .yaml/.yml file with optional top-level keys
            "tables", "charts", "views", "home_view" — matching create_app()'s
            tables/charts/views/home_view parameters — plus an optional
            "scenarios" key (dict of scenario label -> constructor kwargs) and,
            alongside it, an optional "compare" key (dict with "tables",
            "charts" and/or "views" sub-dicts) defining cross-scenario
            comparison artifacts for the explorer's compare mode.
        base_model: The model already loaded from the target .py file. Only
            required when the config declares "scenarios" — used to derive
            the model class and periods for building each scenario instance.

    Returns:
        dict with keys "tables", "charts", "views", "home_view", ready to pass
        as create_app(model, **load_view_config(path)). If the config declares
        "scenarios", the dict also has a "models" key (dict of label ->
        ProformaModel, including "Base" for base_model itself) and
        "compare_tables"/"compare_charts"/"compare_views" keys, ready to pass
        as create_scenario_app(**load_view_config(path, base_model=model)).

    Raises:
        FileNotFoundError: If path doesn't exist.
        ValueError: If path isn't a .yaml/.yml file, a view component
            references a table/chart ref that isn't defined, "scenarios" is
            declared without a base_model, "scenarios" is empty,
            "scenarios" declares a scenario named "Base", "compare" is
            declared without "scenarios", a compare table/chart references
            a line item that isn't common to every scenario, or a compare
            view references an undefined compare table/chart.
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
    compare = raw.get("compare")

    if compare is not None and scenarios is None:
        raise ValueError(f"{path} declares 'compare' but no 'scenarios' — compare mode needs both.")

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

        compare_tables, compare_charts, compare_views = _load_compare(compare or {}, models)
        result["compare_tables"] = compare_tables
        result["compare_charts"] = compare_charts
        result["compare_views"] = compare_views

    return result


def _load_compare(compare: dict, models: dict) -> tuple[dict, dict, dict]:
    """Parse a config's `compare:` block.

    Returns (compare_tables, compare_charts, compare_views):
    - compare_tables: title -> CompareTableDef
    - compare_charts: title -> CompareChartDef
    - compare_views: title -> list of component rows (each component a dict
      {"type": "table"|"chart", "ref": <compare_tables/compare_charts key>})

    Validates every referenced line item against the set common to all
    scenarios, and every view component ref against the compare tables/charts.
    """
    unknown = set(compare) - {"tables", "charts", "views"}
    if unknown:
        raise ValueError(
            f"compare: unknown key(s) {sorted(unknown)}. Allowed: tables, charts, views."
        )

    common_items = set(next(iter(models.values())).line_item_names)
    for model in models.values():
        common_items &= set(model.line_item_names)

    def _check(names, ctx):
        missing = [n for n in names if n not in common_items]
        if missing:
            raise ValueError(
                f"{ctx} references line item(s) {missing} not common to all scenarios."
            )

    compare_tables = {}
    for title, data in (compare.get("tables") or {}).items():
        table_def = CompareTableDef.from_dict(title, data or {})
        _check(table_def.items, f"compare table '{title}'")
        compare_tables[title] = table_def

    compare_charts = {}
    for title, data in (compare.get("charts") or {}).items():
        chart_def = CompareChartDef.from_dict(title, data or {})
        _check([chart_def.item], f"compare chart '{title}'")
        compare_charts[title] = chart_def

    compare_views = {}
    for title, row_defs in (compare.get("views") or {}).items():
        rows = []
        for row_def in row_defs:
            row = []
            for comp in row_def:
                ctype = comp.get("type")
                ref = comp.get("ref")
                if ctype not in ("table", "chart"):
                    raise ValueError(
                        f"compare view '{title}': component type '{ctype}' must be "
                        f"'table' or 'chart'."
                    )
                refs = compare_tables if ctype == "table" else compare_charts
                if ref not in refs:
                    raise ValueError(
                        f"compare view '{title}' references unknown compare {ctype} '{ref}'."
                    )
                row.append({"type": ctype, "ref": ref})
            rows.append(row)
        compare_views[title] = rows

    return compare_tables, compare_charts, compare_views
