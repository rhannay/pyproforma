from typing import TYPE_CHECKING

from pyproforma.table import format_value

if TYPE_CHECKING:
    from pyproforma.proforma_model import ProformaModel


class ScalarResult:
    """Read-only wrapper for a scalar line item value."""

    def __init__(self, model: "ProformaModel", name: str):
        self._model = model
        self._name = name
        self._spec = getattr(type(model), name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> float:
        return self._model._scalars[self._name]

    @property
    def label(self) -> str | None:
        return self._spec.label

    @property
    def value_format(self):
        return self._spec.value_format

    @property
    def formatted_value(self) -> str:
        return format_value(self.value, self.value_format)

    def __float__(self):
        return float(self.value)

    def __repr__(self):
        return f"ScalarResult(name={self._name!r}, value={self.value})"
