"""Flask app factory for exploring a ProformaModel in a web browser."""

import os

from flask import Flask, abort, render_template

from pyproforma.line_items.fixed_line import FixedLine
from pyproforma.line_items.formula_line import FormulaLine
from pyproforma.line_items.debt_line import DebtBase
from pyproforma.assumption import Assumption


def create_app(model):
    """Create a Flask app for exploring a ProformaModel.

    Args:
        model: An instantiated ProformaModel.

    Returns:
        Flask app instance.

    Usage:
        from pyproforma import ProformaModel, FixedLine
        from flask_pyproforma import create_app

        class MyModel(ProformaModel):
            revenue = FixedLine(values={2024: 100_000, 2025: 110_000})

        model = MyModel(periods=[2024, 2025])
        app = create_app(model)
        app.run(debug=True)
    """
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

    @app.route("/")
    def index():
        items = []
        for name in model.line_item_names:
            li = model[name]
            item_def = getattr(type(model), name)
            items.append({
                "name": name,
                "label": item_def.label or name,
                "type": type(item_def).__name__,
                "tags": item_def.tags,
            })
        assumptions = []
        for name in model.assumption_names:
            a = model[name]
            item_def = getattr(type(model), name)
            assumptions.append({
                "name": name,
                "label": item_def.label or name,
                "value": a.value,
            })
        return render_template("index.html", model=model, items=items, assumptions=assumptions)

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
            info["fixed_values"] = item_def.values or {}
        elif isinstance(item_def, DebtBase):
            info["principal"] = item_def.principal
            info["rate"] = item_def.rate
            info["term"] = item_def.term

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
