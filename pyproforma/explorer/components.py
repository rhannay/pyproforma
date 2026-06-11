"""
Explorer components — declarative definitions for view components.

Each component has a build(model) method that returns a dict of render data
consumed by the view template. The template handles all HTML.

Components:
    StatCard   — displays a single aggregated line item value (min, max, first, latest).
    InputGroup — renders a form for a subset of the model's input line items.
"""

from dataclasses import dataclass


@dataclass
class StatCard:
    """
    Displays a single aggregated value from a line item.

    Args:
        name: Line item name.
        label: Display label. Defaults to the line item's own label.
        aggregation: One of "min", "max", "latest", "first". Defaults to "latest".
        value_format: Optional format override. Uses the line item's format if not set.

    Examples:
        >>> StatCard("dscr", "Min DSCR", aggregation="min")
        >>> StatCard("ending_cash", aggregation="latest")
    """

    name: str
    label: str | None = None
    aggregation: str = "latest"
    value_format: object = None

    def build(self, model) -> dict:
        result = model[self.name]
        formatted = getattr(result.stat, f"formatted_{self.aggregation}")(self.value_format)
        return {
            "type": "stat",
            "label": self.label or result.label or self.name,
            "value": formatted,
        }


@dataclass
class InputGroup:
    """
    Renders a form for a subset of the model's input line items inside a view.

    Only ScalarInputLine and InputLine items may be listed. Place alongside
    charts or tables in a view row to show cause and effect on one screen.
    At most one InputGroup is allowed per view (enforced at create_app() time).

    Args:
        names: Input item names to expose. Each must be a ScalarInputLine or InputLine;
            FixedLine and FormulaLine names raise ValueError at build() time.
        label: Optional card header label.
        orient: Layout direction. ``"vertical"`` (default) stacks years top-to-bottom
            inside a narrow card — suited for sharing a row with a chart.
            ``"horizontal"`` puts years as columns in a table, with scalars above;
            best when the InputGroup spans the full row width with output rows below.

    Raises:
        ValueError: If ``orient`` is not ``"vertical"`` or ``"horizontal"``.
        ValueError: If any name in ``names`` is not a ScalarInputLine or InputLine.

    Examples:
        >>> InputGroup(names=["rate_increase"], label="Rate Increases")
        >>> InputGroup(names=["rate_increase"], orient="horizontal")
        >>> InputGroup(names=["inflation_rate", "new_bond_rate", "rate_increase"],
        ...            label="Scenario Inputs", orient="horizontal")
    """

    names: list
    label: str | None = None
    orient: str = "vertical"

    _VALID_ORIENTS = frozenset({"vertical", "horizontal"})

    def __post_init__(self):
        if self.orient not in self._VALID_ORIENTS:
            raise ValueError(
                f"orient must be 'vertical' or 'horizontal', got '{self.orient}'."
            )

    def build(self, model) -> dict:
        valid_scalar = set(model.__class__._scalar_input_names)
        valid_line = set(model.__class__._input_line_names)
        inputs = []
        for name in self.names:
            if name in valid_scalar:
                spec = getattr(type(model), name)
                inputs.append({
                    "name": name,
                    "label": spec.label or name,
                    "is_scalar": True,
                    "value": model._scalars[name],
                    "formatted_value": model[name].formatted_value,
                })
            elif name in valid_line:
                spec = getattr(type(model), name)
                period_values = model._input_line_values.get(name, {})
                locked = set(spec.locked_values)
                inputs.append({
                    "name": name,
                    "label": spec.label or name,
                    "is_scalar": False,
                    "value": period_values,
                    "formatted_values": [model[name].formatted_value(p) for p in model.periods],
                    "periods": model.periods,
                    "editable": [
                        p not in locked and period_values.get(p) is not None
                        for p in model.periods
                    ],
                })
            else:
                raise ValueError(
                    f"'{name}' is not an input item. "
                    f"InputGroup only accepts ScalarInputLine or InputLine names."
                )
        return {
            "type": "input_group",
            "label": self.label,
            "orient": self.orient,
            "periods": model.periods,
            "inputs": inputs,
        }
