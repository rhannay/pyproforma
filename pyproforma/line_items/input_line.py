"""
InputLine class for line items whose values are provided at model instantiation.

InputLine is declared in the model class body like FixedLine, but its values
are supplied as keyword arguments when the model is instantiated. This makes
the model's scenario inputs explicit and enforced.
"""

from typing import Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

# Sentinel distinguishing "no default supplied" from default=None
_MISSING = object()


class InputLine(LineItem):
    """
    A line item whose values are provided at model instantiation.

    InputLine is declared in the model class body with metadata only (label,
    tags, value_format) and an optional default period-value dict. Values are
    supplied as keyword arguments when instantiating the model. If a default is
    provided, the kwarg may be omitted and the default is used instead.

    Unlike FixedLine (values baked into the class), InputLine values vary
    per model instance — they are the "knobs" of the model.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     # Required input — no default, must be provided at instantiation
        ...     revenue = InputLine(label="Revenue", value_format=Format.CURRENCY)
        ...
        ...     # Optional input — has a default schedule, can be overridden
        ...     rate_increase = InputLine(
        ...         default={2024: 0.05, 2025: 0.04},
        ...         label="Rate Increase",
        ...         value_format=Format.PERCENT,
        ...     )
        ...
        >>> base = MyModel(periods=[2024, 2025], revenue={2024: 1_000_000, 2025: 1_100_000})
        >>> high_rate = MyModel(
        ...     periods=[2024, 2025],
        ...     revenue={2024: 1_000_000, 2025: 1_100_000},
        ...     rate_increase={2024: 0.08, 2025: 0.08},
        ... )

    Attributes:
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
        value_format (NumberFormatSpec): Format specification for displaying values.
    """

    def __init__(
        self,
        default: dict | None = _MISSING,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize an InputLine.

        Args:
            default (dict[int, float], optional): Default period-value mapping used
                when no value is supplied at instantiation. Omit to make the input
                required.
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
            value_format (str | NumberFormatSpec | dict, optional):
                Format specification for displaying values.
                Defaults to None (inherits default 'no_decimals').
        """
        super().__init__(label=label, tags=tags, value_format=value_format)
        self._default = default

    @property
    def has_default(self) -> bool:
        """True if a default period-value dict was provided."""
        return self._default is not _MISSING

    @property
    def default(self) -> dict:
        """The default period-value dict, or raises AttributeError if none was set."""
        if self._default is _MISSING:
            raise AttributeError(
                f"InputLine '{self.name}' has no default value."
            )
        return self._default

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
        parts = []
        if self.has_default:
            parts.append(f"default={self._default!r}")
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"InputLine({', '.join(parts)})"
