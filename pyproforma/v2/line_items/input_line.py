"""
InputLine class for line items whose values are provided at model instantiation.

InputLine is declared in the model class body like FixedLine, but its values
are supplied as keyword arguments when the model is instantiated. This makes
the model's scenario inputs explicit and enforced.
"""

from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem


class InputLine(LineItem):
    """
    A line item whose values are provided at model instantiation.

    InputLine is declared in the model class body with metadata only (label,
    tags, value_format). Values are supplied as keyword arguments when
    instantiating the model, making scenario inputs explicit and required.

    Unlike FixedLine (values baked into the class), InputLine values vary
    per model instance — they are the "knobs" of the model.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     # Structural assumption — fixed, not a scenario input
        ...     fixed_costs = FixedLine(values={2024: 50000, 2025: 52000})
        ...
        ...     # Scenario inputs — must be provided at instantiation
        ...     revenue = InputLine(label="Revenue", value_format=Format.CURRENCY)
        ...
        ...     profit = FormulaLine(
        ...         formula=lambda a, li, t: li.revenue[t] - li.fixed_costs[t]
        ...     )
        ...
        >>> base = MyModel(periods=[2024, 2025], revenue={2024: 1_000_000, 2025: 1_100_000})
        >>> bull = MyModel(periods=[2024, 2025], revenue={2024: 1_400_000, 2025: 1_600_000})

    Attributes:
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
        value_format (NumberFormatSpec): Format specification for displaying values.
    """

    def __init__(
        self,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize an InputLine.

        Args:
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
            value_format (str | NumberFormatSpec | dict, optional):
                Format specification for displaying values.
                Defaults to None (inherits default 'no_decimals').
        """
        super().__init__(label=label, tags=tags, value_format=value_format)

    def get_value(self, period: int) -> float | None:
        """
        Not used directly — values are resolved via the model instance.

        InputLine values are stored on the model instance at instantiation
        and accessed by the calculation engine via model._input_line_values.

        Raises:
            NotImplementedError: Always — use model.get_value(name, period) instead.
        """
        raise NotImplementedError(
            "InputLine values are resolved at model instantiation. "
            "Use model.get_value(name, period) instead."
        )

    def __repr__(self):
        """Return a string representation of the InputLine."""
        if self.label:
            return f"InputLine(label={self.label!r})"
        return "InputLine()"
