"""Flask app factory for exploring N named scenarios of one ProformaModel class."""

import json
import os
import sys

from flask import Blueprint, Flask, abort, redirect, render_template, url_for

from pyproforma.compare import ModelComparison
from pyproforma.explorer.app import _register_model_routes
from pyproforma.explorer.components import InputGroup
from pyproforma.table import Cell, Table
from pyproforma.tables.row_types import HeaderRow, ItemRow
from pyproforma.tables.table_def import TableDef


def _drop_input_groups(views):
    """Strip InputGroup components out of a views config, warning on stderr.

    Scenario mode is read-only (no input editing), so InputGroup components
    from a views config shared with single-model mode aren't renderable here.
    """
    filtered = {}
    for view_label, rows in (views or {}).items():
        new_rows = []
        for row in rows:
            new_row = [comp for comp in row if not isinstance(comp, InputGroup)]
            if len(new_row) != len(row):
                print(
                    f"Warning: input groups are not supported in scenario mode — "
                    f"dropping component in view '{view_label}'",
                    file=sys.stderr,
                )
            if new_row:
                new_rows.append(new_row)
        filtered[view_label] = new_rows
    return filtered


def _build_scenario_inputs_table(models, labels) -> Table:
    """Build a table of every input that differs across the given scenarios.

    Each differing input gets its own section, read top to bottom: a header
    row of column labels, a title row naming the input, and one row per
    scenario. For period-varying inputs the columns are the periods that
    actually differ (years running across the top); for scalars the columns
    are the scenario labels, since there's no period axis to lay out. Inputs
    with the same value everywhere are omitted.
    """
    model_class = type(models[labels[0]])
    periods = models[labels[0]].periods

    blocks = []

    scalar_rows = []
    for name in model_class._scalar_input_names:
        spec = getattr(model_class, name)
        values = {label: models[label]._scalars[name] for label in labels}
        if len(set(values.values())) > 1:
            scalar_rows.append(
                (spec.label or name, [values[label] for label in labels], spec.value_format)
            )
    if scalar_rows:
        blocks.append(
            {"title": "Scalars", "corner": "", "col_headers": labels, "rows": scalar_rows}
        )

    for name in model_class._input_line_names:
        spec = getattr(model_class, name)
        period_values = {
            label: models[label]._input_line_values.get(name, {}) for label in labels
        }
        differing_periods = [
            period
            for period in periods
            if len({period_values[label].get(period) for label in labels}) > 1
        ]
        if not differing_periods:
            continue
        rows = [
            (
                label,
                [period_values[label].get(period) for period in differing_periods],
                spec.value_format,
            )
            for label in labels
        ]
        blocks.append(
            {
                "title": spec.label or name,
                "corner": "Period",
                "col_headers": differing_periods,
                "rows": rows,
            }
        )

    if not blocks:
        return Table(cells=[[Cell(value="No differing inputs across scenarios.", align="left")]])

    n_cols = 1 + max(len(block["col_headers"]) for block in blocks)

    def pad(cells):
        cells = list(cells)
        while len(cells) < n_cols:
            cells.append(Cell(value=""))
        return cells

    rows = []
    for i, block in enumerate(blocks):
        if i > 0:
            rows.append(pad([Cell(value="")]))
        header = [Cell(value=block["corner"], bold=True, align="left")]
        header += [Cell(value=h, bold=True, align="center") for h in block["col_headers"]]
        rows.append(pad(header))
        rows.append(pad([Cell(value=block["title"], bold=True, align="left")]))
        for row_label, values, value_format in block["rows"]:
            row = [Cell(value=row_label, align="left")]
            row += [Cell(value=v, value_format=value_format) for v in values]
            rows.append(pad(row))

    return Table(cells=rows)


def _compare_table(comparison, spec):
    """Build the comparison Table for a CompareTableDef."""
    return comparison.table(
        spec.items or None,
        include_values=spec.include_values,
        include_difference=spec.include_difference,
        include_percent_difference=spec.include_percent_difference,
    )


def _compare_chart_apex(comparison, spec):
    """Build the ApexCharts spec dict for a CompareChartDef."""
    return comparison.chart(
        spec.item, chart_type=spec.chart_type, title=spec.title
    ).to_apexcharts()


def _build_scenario_state(model, tables, charts, views, home_view, excel_available):
    class _State:
        pass

    state = _State()
    state.model = model

    all_items_def = TableDef(
        rows=[HeaderRow(), *[ItemRow(name=n) for n in model.line_item_names]],
        title="All Line Items",
    )
    state.tables = {"All Line Items": all_items_def, **(tables or {})}
    state.charts = charts or {}
    state.views = views
    state.home_view = home_view
    state.excel_available = excel_available
    return state


def create_scenario_app(
    models,
    *,
    tables=None,
    charts=None,
    views=None,
    home_view=None,
    compare_tables=None,
    compare_charts=None,
    compare_views=None,
):
    """Create a Flask app for browsing N named scenarios of one ProformaModel class.

    Every scenario shares the same tables/charts/views config, browsable
    read-only under /scenario/<label>/..., plus a /compare area whose top nav
    mirrors the scenario nav: an auto-generated differing-inputs overview, a
    browsable list of common line items, and any curated cross-scenario
    comparison tables/charts from the config's `compare:` block.

    Args:
        models: Dict of label → ProformaModel instance. All must be the same
            model class (built by pyproforma.explorer.config.load_view_config
            from a "scenarios" YAML block). Must have at least 2 entries.
        tables: Dict of label → TableDef for the Tables nav section.
        charts: Dict of label → ChartDef for the Charts nav section.
        views: Dict of label → view definition for the Views nav section. Any
            InputGroup component is dropped with a stderr warning — scenario
            mode has no input editing.
        home_view: Name of a view to show at each scenario's '/' instead of
            the default index. Must match a key in `views`.
        compare_tables: Dict of title → CompareTableDef for compare mode's
            Tables nav section.
        compare_charts: Dict of title → CompareChartDef for compare mode's
            Charts nav section.
        compare_views: Dict of title → list of component rows for compare
            mode's Views nav section. Each component is a dict
            {"type": "table"|"chart", "ref": <compare_tables/compare_charts key>}.

    Returns:
        Flask app instance.
    """
    compare_tables = compare_tables or {}
    compare_charts = compare_charts or {}
    compare_views = compare_views or {}
    if len(models) < 2:
        raise ValueError("scenarios: must declare at least one scenario.")

    if home_view is not None and home_view not in (views or {}):
        available = ", ".join(f"'{v}'" for v in (views or {})) or "none"
        raise ValueError(
            f"home_view '{home_view}' not found in views. Available views: {available}"
        )

    filtered_views = _drop_input_groups(views)

    try:
        import openpyxl  # noqa: F401

        excel_available = True
    except ImportError:
        excel_available = False

    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
    app.secret_key = "pyproforma-explorer"

    labels = list(models.keys())

    for i, label in enumerate(labels):
        if "/" in label:
            raise ValueError(
                f"Scenario label '{label}' must not contain '/' (used as a URL path segment)."
            )
        state = _build_scenario_state(
            models[label], tables, charts, filtered_views, home_view, excel_available
        )
        bp = Blueprint(f"scenario_{i}", __name__, url_prefix=f"/scenario/{label}")

        @bp.context_processor
        def inject_scenario_nav(labels=labels, label=label):
            return {"nav_scenarios": labels, "current_scenario": label}

        _register_model_routes(bp, state, include_inputs=False)
        app.register_blueprint(bp)

    comparison = ModelComparison(*models.values(), labels=labels)
    compare_table_titles = list(compare_tables.keys())
    compare_chart_titles = list(compare_charts.keys())
    compare_view_titles = list(compare_views.keys())
    compare_bp = Blueprint("compare", __name__, url_prefix="/compare")

    @compare_bp.context_processor
    def inject_compare_nav():
        return {
            "nav_tables": list(enumerate(compare_table_titles)),
            "nav_charts": list(enumerate(compare_chart_titles)),
            "nav_views": list(enumerate(compare_view_titles)),
            "nav_tags": [],
            "nav_has_inputs": False,
            "excel_available": excel_available,
            "nav_scenarios": labels,
            "current_scenario": None,
        }

    @compare_bp.route("/")
    def index():
        inputs_table = _build_scenario_inputs_table(models, labels)
        return render_template(
            "compare_overview.html",
            model=models[labels[0]],
            inputs_table_html=inputs_table.to_bootstrap_html(),
        )

    @compare_bp.route("/items")
    def items():
        return render_template(
            "compare_items.html",
            model=models[labels[0]],
            items=comparison.common_items,
        )

    @compare_bp.route("/item/<name>")
    def line_item(name):
        if name not in comparison.common_items:
            abort(404)
        return render_template(
            "compare_item.html",
            model=models[labels[0]],
            name=name,
            table_html=comparison.table([name]).to_bootstrap_html(),
            chart_data=json.dumps(comparison.chart(name).to_apexcharts()),
        )

    @compare_bp.route("/table/<int:idx>")
    def table_view(idx):
        if idx >= len(compare_table_titles):
            abort(404)
        spec = compare_tables[compare_table_titles[idx]]
        return render_template(
            "table_view.html",
            model=models[labels[0]],
            title=spec.title,
            table_html=_compare_table(comparison, spec).to_bootstrap_html(),
            download_url=None,
        )

    @compare_bp.route("/chart/<int:idx>")
    def chart_view(idx):
        if idx >= len(compare_chart_titles):
            abort(404)
        spec = compare_charts[compare_chart_titles[idx]]
        return render_template(
            "chart_view.html",
            model=models[labels[0]],
            title=spec.title,
            chart_data=json.dumps(_compare_chart_apex(comparison, spec)),
        )

    @compare_bp.route("/view/<int:idx>")
    def view_page(idx):
        if idx >= len(compare_view_titles):
            abort(404)
        title = compare_view_titles[idx]
        rows = []
        for row_idx, row in enumerate(compare_views[title]):
            col_width = 12 // len(row)
            processed = []
            for col_idx, comp in enumerate(row):
                c = dict(comp)
                c["col_width"] = col_width
                if comp["type"] == "chart":
                    spec = compare_charts[comp["ref"]]
                    c["chart_data"] = json.dumps(_compare_chart_apex(comparison, spec))
                    c["chart_id"] = f"compare-view-chart-{row_idx}-{col_idx}"
                else:  # table
                    spec = compare_tables[comp["ref"]]
                    c["html"] = _compare_table(comparison, spec).to_bootstrap_html()
                    c["table_title"] = spec.title
                    c["download_url"] = None
                processed.append(c)
            rows.append(processed)
        return render_template(
            "view.html",
            model=models[labels[0]],
            title=title,
            rows=rows,
            has_inputs=False,
            form_action=None,
        )

    app.register_blueprint(compare_bp)

    @app.route("/")
    def root_redirect():
        # Land on the base scenario (the first one declared), not compare mode.
        return redirect(url_for("scenario_0.index"))

    return app
