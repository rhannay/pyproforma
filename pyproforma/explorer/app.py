"""Flask app factory for exploring a ProformaModel in a web browser."""

import dataclasses
import json
import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from pyproforma.explorer.components import StatCard
from pyproforma.specs.fixed_line import FixedLine
from pyproforma.specs.formula_line import FormulaLine
from pyproforma.specs.input_line import InputLine
from pyproforma.specs.scalar_input_line import ScalarInputLine
from pyproforma.specs.scalar_line import ScalarLine
from pyproforma.table import Format
from pyproforma.tables.row_types import HeaderRow, ItemRow, TagItemsRow
from pyproforma.tables.table_def import TableDef


def create_app(model, *, tables=None, charts=None, views=None, home_view=None):
    """Create a Flask app for exploring a ProformaModel.

    Args:
        model: An instantiated ProformaModel.
        tables: Dict of label → TableDef for the Tables nav section.
        charts: Dict of label → ChartDef for the Charts nav section.
        views: Dict of label → view definition for the Views nav section.
        home_view: Name of a view to show at '/' instead of the default index.
            Must match a key in `views`. If None or not found, the default
            line item index is shown.

    Returns:
        Flask app instance.

    Usage:
        from pyproforma import ProformaModel, FixedLine
        from pyproforma.explorer import create_app

        class MyModel(ProformaModel):
            revenue = FixedLine(values={2024: 100_000, 2025: 110_000})

        model = MyModel(periods=[2024, 2025])
        app = create_app(model, home_view="Financial Summary")
        app.run(debug=True)
    """
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
    app.secret_key = "pyproforma-explorer"

    class _State:
        pass

    state = _State()
    state.model = model
    state.model_class = type(model)
    state.periods = model.periods
    state.error = None

    all_items_def = TableDef(
        rows=[HeaderRow(), *[ItemRow(name=n) for n in model.line_item_names]],
        title="All Line Items",
    )
    state.tables = {"All Line Items": all_items_def, **(tables or {})}
    state.charts = charts or {}
    state.views = views or {}
    if home_view is not None and home_view not in (views or {}):
        available = ", ".join(f"'{v}'" for v in (views or {})) or "none"
        raise ValueError(
            f"home_view '{home_view}' not found in views. "
            f"Available views: {available}"
        )
    state.home_view = home_view

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @app.context_processor
    def inject_nav():
        return {
            "nav_tables": list(enumerate(state.tables.keys())),
            "nav_charts": list(enumerate(state.charts.keys())),
            "nav_views": list(enumerate(state.views.keys())),
            "nav_tags": state.model.tags,
        }

    def _format_name(spec):
        if spec is None:
            return "—"
        for name, standard in Format._STRING_MAP.items():
            if spec == standard:
                return name.upper()
        return str(spec)

    def _build_items(names, scalar_names=None):
        m = state.model
        items = []
        for name in names:
            item_def = getattr(type(m), name)
            items.append({
                "name": name,
                "label": item_def.label or name,
                "type": type(item_def).__name__,
                "tags": getattr(item_def, "tags", []),
                "scalar": False,
            })
        for name in (scalar_names or []):
            item_def = getattr(type(m), name)
            items.append({
                "name": name,
                "label": item_def.label or name,
                "type": type(item_def).__name__,
                "tags": [],
                "scalar": True,
                "value": m[name].formatted_value,
            })
        return items

    def _build_inputs():
        m = state.model
        inputs = []
        for name in state.model_class._scalar_input_names:
            spec = getattr(state.model_class, name)
            inputs.append({
                "name": name,
                "label": spec.label or name,
                "is_scalar": True,
                "value": m._scalars[name],
                "formatted_values": [m[name].formatted_value],
            })
        for name in state.model_class._input_line_names:
            spec = getattr(state.model_class, name)
            inputs.append({
                "name": name,
                "label": spec.label or name,
                "is_scalar": False,
                "value": m._input_line_values.get(name, {}),
                "formatted_values": [m[name].formatted_value(p) for p in state.periods],
            })
        return inputs

    def _add_hrefs(definition):
        rows = definition.rows if isinstance(definition, TableDef) else definition
        result = []
        for row in rows:
            if isinstance(row, ItemRow):
                result.append(dataclasses.replace(row, href=url_for("line_item", name=row.name)))
            elif isinstance(row, TagItemsRow):
                names = [n for n in state.model.line_item_names
                         if row.tag in getattr(type(state.model), n).tags]
                for name in names:
                    result.append(ItemRow(name=name, bold=row.bold,
                                          href=url_for("line_item", name=name)))
            else:
                result.append(row)
        if isinstance(definition, TableDef):
            return TableDef(rows=result, title=definition.title)
        return result

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    def _render_line_items_index():
        m = state.model
        return render_template(
            "index.html",
            model=m,
            items=_build_items(m.line_item_names, m.scalar_names),
            title=m.__class__.__name__,
        )

    @app.route("/")
    def index():
        if state.home_view is not None:
            view_labels = list(state.views.keys())
            if state.home_view in view_labels:
                return redirect(url_for("view_page", idx=view_labels.index(state.home_view)))
        return _render_line_items_index()

    @app.route("/items")
    def items():
        return _render_line_items_index()

    @app.route("/tag/<tag_name>")
    def tag_view(tag_name):
        m = state.model
        names = [n for n in m.line_item_names if tag_name in getattr(type(m), n).tags]
        if not names:
            abort(404)

        tag_template = [
            HeaderRow(),
            TagItemsRow(tag=tag_name, include_total_row=True,
                        total_row_label=f"Total {tag_name}"),
        ]
        tag_table_html = m.tables.build(_add_hrefs(tag_template)).to_bootstrap_html()
        tag_chart_data = json.dumps(
            m.charts.line_items(names, chart_type="stacked_bar", title=tag_name).to_apexcharts()
        ) if m.periods else None

        return render_template(
            "index.html",
            model=m,
            items=_build_items(names),
            title=f"Tag: {tag_name}",
            back_link=True,
            tag_table_html=tag_table_html,
            tag_chart_data=tag_chart_data,
        )

    @app.route("/line_item/<name>")
    def line_item(name):
        m = state.model
        is_scalar = name in m.scalar_names
        if name not in m.line_item_names and not is_scalar:
            abort(404)
        item_def = getattr(type(m), name)

        info = {
            "name": name,
            "label": item_def.label or name,
            "type": type(item_def).__name__,
            "tags": getattr(item_def, "tags", []),
            "value_format": _format_name(item_def.value_format),
        }

        dependents = m.dependents(name)

        if is_scalar:
            info["scalar_value"] = m[name].formatted_value
            return render_template(
                "line_item.html",
                model=m,
                info=info,
                values_table=None,
                precedents_table=None,
                chart_data=None,
                dependents=dependents,
            )

        if isinstance(item_def, FormulaLine):
            info["formula_source"] = item_def.formula_source
            info["dependencies"] = item_def.precedents or []
            info["tag_dependencies"] = {
                tag: m.tag[tag].names
                for tag in (item_def.tag_references or [])
            }
        elif isinstance(item_def, FixedLine):
            info["fixed_values"] = item_def.values or {}
        elif isinstance(item_def, InputLine):
            info["input_values"] = m._input_line_values.get(name, {})
            info["is_input"] = True

        values_table = m.tables.line_item(name).to_bootstrap_html()

        precedents_table = None
        if isinstance(item_def, FormulaLine) and item_def.precedents:
            precedents_table = m.tables.precedents(name).to_bootstrap_html()

        chart_data = json.dumps(m.charts.line_item(name).to_apexcharts()) if m.periods else None

        return render_template(
            "line_item.html",
            model=m,
            info=info,
            values_table=values_table,
            precedents_table=precedents_table,
            chart_data=chart_data,
            dependents=dependents,
        )

    @app.route("/table/<int:idx>")
    def table_view(idx):
        labels = list(state.tables.keys())
        if idx >= len(labels):
            abort(404)
        label = labels[idx]
        definition = state.tables[label]
        table = state.model.tables.build(_add_hrefs(definition))
        return render_template(
            "table_view.html",
            model=state.model,
            title=table.title or label,
            table_html=table.to_bootstrap_html(),
        )

    @app.route("/chart/<int:idx>")
    def chart_view(idx):
        labels = list(state.charts.keys())
        if idx >= len(labels):
            abort(404)
        label = labels[idx]
        chart_data = json.dumps(state.model.charts.build(state.charts[label]).to_apexcharts())
        return render_template(
            "chart_view.html",
            model=state.model,
            title=label,
            chart_data=chart_data,
        )

    @app.route("/view/<int:idx>")
    def view_page(idx):
        labels = list(state.views.keys())
        if idx >= len(labels):
            abort(404)
        label = labels[idx]
        view_def = state.views[label]

        rows = []
        for row_idx, row in enumerate(view_def):
            col_width = 12 // len(row)
            processed = []
            for col_idx, comp in enumerate(row):
                if isinstance(comp, StatCard):
                    c = comp.build(state.model)
                    c["col_width"] = col_width
                elif isinstance(comp, dict) and comp.get("type") == "stat":
                    c = StatCard(
                        name=comp["name"],
                        label=comp.get("label"),
                        aggregation=comp.get("aggregation", "latest"),
                    ).build(state.model)
                    c["col_width"] = col_width
                elif comp["type"] == "chart":
                    c = dict(comp)
                    c["col_width"] = col_width
                    c["chart_data"] = json.dumps(
                        state.model.charts.build(state.charts[comp["ref"]]).to_apexcharts()
                    )
                    c["chart_id"] = f"view-chart-{row_idx}-{col_idx}"
                elif comp["type"] == "table":
                    built = state.model.tables.build(_add_hrefs(state.tables[comp["ref"]]))
                    c = dict(comp)
                    c["col_width"] = col_width
                    c["html"] = built.to_bootstrap_html()
                    c["table_title"] = built.title or comp["ref"]
                processed.append(c)
            rows.append(processed)

        return render_template(
            "view.html",
            model=state.model,
            title=label,
            rows=rows,
        )

    @app.route("/inputs", methods=["GET"])
    def inputs():
        m = state.model
        error = state.error
        state.error = None
        return render_template(
            "inputs.html",
            model=m,
            inputs=_build_inputs(),
            error=error,
        )

    @app.route("/inputs", methods=["POST"])
    def update_inputs():
        m = state.model
        kwargs = {}
        try:
            for name in state.model_class._scalar_input_names:
                kwargs[name] = float(request.form[name])
            for name in state.model_class._input_line_names:
                kwargs[name] = {
                    period: float(request.form[f"{name}_{period}"])
                    for period in state.periods
                }
            state.model = state.model_class(periods=state.periods, **kwargs)
            state.error = None
            flash("Model updated.")
        except Exception as e:
            state.error = str(e)
        return redirect(url_for("inputs"))

    return app
