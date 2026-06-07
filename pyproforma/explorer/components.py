"""
Explorer components — declarative definitions for view components.

Each component has a build(model) method that returns a dict of render data
consumed by the view template. The template handles all HTML.

Components:
    StatCard — displays a single aggregated line item value (min, max, first, latest).
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
