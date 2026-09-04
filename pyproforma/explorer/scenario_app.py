"""Flask app factory for exploring N named scenarios of one ProformaModel class."""

import json
import os
import sys

from flask import Blueprint, Flask, abort, redirect, render_template, url_for

from pyproforma.compare import ModelComparison
from pyproforma.explorer.app import _register_model_routes
from pyproforma.explorer.components import InputGroup
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


def create_scenario_app(models, *, tables=None, charts=None, views=None, home_view=None):
    """Create a Flask app for browsing N named scenarios of one ProformaModel class.

    Every scenario shares the same tables/charts/views config, browsable
    read-only under /scenario/<label>/..., plus a /compare area with
    auto-generated per-item diffs across all scenarios.

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

    Returns:
        Flask app instance.
    """
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
    compare_bp = Blueprint("compare", __name__, url_prefix="/compare")

    @compare_bp.context_processor
    def inject_compare_nav():
        return {
            "nav_tables": [],
            "nav_charts": [],
            "nav_views": [],
            "nav_tags": [],
            "nav_has_inputs": False,
            "excel_available": excel_available,
            "nav_scenarios": labels,
            "current_scenario": None,
        }

    @compare_bp.route("/")
    def compare_index():
        return render_template(
            "compare_index.html",
            model=models[labels[0]],
            items=comparison.common_items,
        )

    @compare_bp.route("/<name>")
    def compare_item(name):
        if name not in comparison.common_items:
            abort(404)
        return render_template(
            "compare_item.html",
            model=models[labels[0]],
            name=name,
            table_html=comparison.table([name]).to_bootstrap_html(),
            chart_data=json.dumps(comparison.chart(name).to_apexcharts()),
        )

    app.register_blueprint(compare_bp)

    @app.route("/")
    def root_redirect():
        return redirect(url_for("scenario_0.index"))

    return app
