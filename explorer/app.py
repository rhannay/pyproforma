"""Flask app factory for exploring a ProformaModel in a web browser."""

import os

from flask import Flask, abort, render_template

from pyproforma.line_items.fixed_line import FixedLine
from pyproforma.line_items.formula_line import FormulaLine
from pyproforma.line_items.debt_line import DebtBase


def create_app(model):
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

    def _build_items(names):
        items = []
        for name in names:
            item_def = getattr(type(model), name)
            is_scalar = isinstance(item_def, FixedLine) and item_def.is_scalar
            items.append({
                "name": name,
                "label": item_def.label or name,
                "type": type(item_def).__name__,
                "tags": item_def.tags,
                "scalar": is_scalar,
                "value": model[name].formatted_value(model.periods[0]) if (is_scalar and model.periods) else None,
            })
        return items

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            model=model,
            items=_build_items(model.line_item_names),
            title=model.__class__.__name__,
        )

    @app.route("/tag/<tag_name>")
    def tag_view(tag_name):
        names = [n for n in model.line_item_names if tag_name in getattr(type(model), n).tags]
        if not names:
            abort(404)
        return render_template(
            "index.html",
            model=model,
            items=_build_items(names),
            title=f"Tag: {tag_name}",
            back_link=True,
        )

    @app.route("/line_item/<name>")
    def line_item(name):
        if name not in model.line_item_names:
            abort(404)
        item_def = getattr(type(model), name)
        result = model[name]

        info = {
            "name": name,
            "label": item_def.label or name,
            "type": type(item_def).__name__,
            "tags": item_def.tags,
            "value_format": str(item_def.value_format),
        }

        if isinstance(item_def, FormulaLine):
            info["formula_source"] = item_def.formula_source
            info["dependencies"] = item_def.precedents or []
        elif isinstance(item_def, FixedLine):
            if item_def.is_scalar:
                info["scalar_value"] = result.formatted_value(model.periods[0]) if model.periods else str(item_def._scalar_value)
            else:
                info["fixed_values"] = item_def.values or {}
        elif isinstance(item_def, DebtBase):
            info["principal"] = item_def.principal
            info["rate"] = item_def.rate
            info["term"] = item_def.term

        values_table = None
        if not (isinstance(item_def, FixedLine) and item_def.is_scalar):
            values_table = model.tables.line_item(name).to_bootstrap_html()

        precedents_table = None
        if isinstance(item_def, FormulaLine) and item_def.precedents:
            precedents_table = model.tables.precedents(name).to_bootstrap_html()

        return render_template(
            "line_item.html",
            model=model,
            info=info,
            values_table=values_table,
            precedents_table=precedents_table,
        )

    return app
