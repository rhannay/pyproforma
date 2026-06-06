"""TagNamespace — user-facing tag accessor returned by model.tag."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.results.line_item_selection import LineItemSelection
    from pyproforma.proforma_model import ProformaModel


class TagNamespace:
    """
    Returned by ``model.tag``; maps a tag name to a LineItemSelection.

    Examples:
        >>> model.tag["revenue"].names
        ['coffee_sales', 'food_sales']
        >>> model.tag["revenue"].sum(2024)
        375000
    """

    def __init__(self, model: "ProformaModel"):
        self._model = model

    def __getitem__(self, tag: str) -> "LineItemSelection":
        from pyproforma.results.line_item_selection import LineItemSelection

        matching = [
            name for name in self._model.line_item_names
            if tag in getattr(self._model.__class__, name).tags
        ]
        return LineItemSelection(self._model, matching)

    def __repr__(self):
        return f"TagNamespace(model={self._model.__class__.__name__})"
