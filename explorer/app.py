"""Flask app factory for exploring a ProformaModel in a web browser."""

import json
import os

import dataclasses

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from pyproforma.line_items.fixed_line import FixedLine
from pyproforma.tables.row_types import ItemRow, TagItemsRow
from pyproforma.table import Format
from pyproforma.line_items.formula_line import FormulaLine
from pyproforma.line_items.input_line import InputLine


def create_app(model, tables=None):
    """Create a Flask app for exploring a ProformaModel.

    Args:
        model: An instantiated ProformaModel.

    Returns:
        Flask app instance.

    Usage:
        from pyproforma import ProformaModel, FixedLine
        from explorer import create_app

        class MyModel(ProformaModel):
            revenue = FixedLine(values={2024: 100_000, 2025: 110_000})

        model = MyModel(periods=[2024, 2025])
        app = create_app(model)
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
    state.tables = tables or {}  # {label: template}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @app.context_processor
    def inject_nav():
        return {"nav_tables": list(enumerate(state.tables.keys()))}

    def _format_name(spec):
        if spec is None:
            return "—"
        for name, standard in Format._STRING_MAP.items():
            if spec == standard:
                return name.upper()
        return str(spec)

    def _build_items(names):
        m = state.model
        items = []
        for name in names:
            item_def = getattr(type(m), name)
            is_scalar = isinstance(item_def, FixedLine) and item_def.is_scalar
            items.append({
                "name": name,
                "label": item_def.label or name,
                "type": type(item_def).__name__,
                "tags": item_def.tags,
                "scalar": is_scalar,
                "value": m[name].formatted_value(m.periods[0]) if (is_scalar and m.periods) else None,
            })
        return items

    def _build_inputs():
        m = state.model
        inputs = []
        for name in state.model_class._input_line_names:
            spec = getattr(state.model_class, name)
            is_scalar = name in m._scalars
            inputs.append({
                "name": name,
                "label": spec.label or name,
                "is_scalar": is_scalar,
                "value": m._scalars[name] if is_scalar else m._input_line_values.get(name, {}),
            })
        return inputs

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        m = state.model
        return render_template(
            "index.html",
            model=m,
            items=_build_items(m.line_item_names),
            title=m.__class__.__name__,
        )

    @app.route("/tag/<tag_name>")
    def tag_view(tag_name):
        m = state.model
        names = [n for n in m.line_item_names if tag_name in getattr(type(m), n).tags]
        if not names:
            abort(404)
        return render_template(
            "index.html",
            model=m,
            items=_build_items(names),
            title=f"Tag: {tag_name}",
            back_link=True,
        )

    @app.route("/line_item/<name>")
    def line_item(name):
        m = state.model
        if name not in m.line_item_names:
            abort(404)
        item_def = getattr(type(m), name)
        result = m[name]

        info = {
            "name": name,
            "label": item_def.label or name,
            "type": type(item_def).__name__,
            "tags": item_def.tags,
            "value_format": _format_name(item_def.value_format),
        }

        if isinstance(item_def, FormulaLine):
            info["formula_source"] = item_def.formula_source
            info["dependencies"] = item_def.precedents or []
            info["tag_dependencies"] = {
                tag: m.tag[tag].names
                for tag in (item_def.tag_references or [])
            }
        elif isinstance(item_def, FixedLine):
            if item_def.is_scalar:
                info["scalar_value"] = result.formatted_value(m.periods[0]) if m.periods else str(item_def._scalar_value)
            else:
                info["fixed_values"] = item_def.values or {}
        elif isinstance(item_def, InputLine):
            is_scalar = name in m._scalars
            if is_scalar:
                info["scalar_value"] = result.formatted_value(m.periods[0]) if m.periods else str(m._scalars[name])
            else:
                info["input_values"] = m._input_line_values.get(name, {})
            info["is_input"] = True

        values_table = None
        scalar_input = isinstance(item_def, InputLine) and name in m._scalars
        scalar_fixed = isinstance(item_def, FixedLine) and item_def.is_scalar
        if not (scalar_input or scalar_fixed):
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
        )

    def _add_hrefs(template):
        result = []
        for row in template:
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
        return result

    @app.route("/table/<int:idx>")
    def table_view(idx):
        labels = list(state.tables.keys())
        if idx >= len(labels):
            abort(404)
        label = labels[idx]
        template = state.tables[label]
        table_html = state.model.tables.from_template(_add_hrefs(template)).to_bootstrap_html()
        return render_template(
            "table_view.html",
            model=state.model,
            title=label,
            table_html=table_html,
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
            for name in state.model_class._input_line_names:
                is_scalar = name in m._scalars
                if is_scalar:
                    kwargs[name] = float(request.form[name])
                else:
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
