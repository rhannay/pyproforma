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

    The ``values`` parameter locks specific periods with memorized actuals.
    Locked periods cannot be overridden at instantiation and are shown as
    greyed-out (non-editable) in Explorer InputGroups. Use ``None`` in
    ``default`` for periods that are not applicable at all (e.g. a first
    period whose consuming formula is seeded directly).

    Examples:
        >>> class MyModel(ProformaModel):
        ...     # Required input — no default, must be provided at instantiation
        ...     revenue = InputLine(label="Revenue", value_format=Format.CURRENCY)
        ...
        ...     # Memorialize a known actual for 2024; 2025 onward is user-editable
        ...     rate_increase = InputLine(
        ...         values={2024: 0.05},
        ...         default={2025: 0.04, 2026: 0.04},
        ...         label="Rate Increase",
        ...         value_format=Format.PERCENT,
        ...     )
        ...
        ...     # 2024 is not applicable (consuming formula is seeded that year)
        ...     capex = InputLine(
        ...         default={2024: None, 2025: 5_000_000},
        ...         label="Capital Expenditures",
        ...     )

    Attributes:
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
        value_format (NumberFormatSpec): Format specification for displaying values.
    """

    def __init__(
        self,
        values: dict | None = None,
        default: dict | None = _MISSING,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize an InputLine.

        Args:
            values (dict[int, float], optional): Locked period-value mapping for
                memorized actuals. These periods cannot be overridden at instantiation
                and are shown as read-only in Explorer. A period must not appear in
                both values and default.
            default (dict[int, float | None], optional): Default period-value mapping
                used when no kwarg is supplied. Periods mapped to None are treated as
                not applicable — they cannot be overridden and show as "—" in Explorer.
                Omit to make the input required.
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
            value_format (str | NumberFormatSpec | dict, optional):
                Format specification for displaying values.

        Raises:
            TypeError: If default is not a dict.
            ValueError: If a period appears in both values and default.
        """
        if default is not _MISSING and not isinstance(default, dict):
            raise TypeError(
                "InputLine default must be a dict mapping periods to values. "
                "For a scalar constant use ScalarInputLine instead."
            )
        if values and default is not _MISSING:
            overlap = sorted(set(values) & set(default))
            if overlap:
                raise ValueError(
                    f"Period(s) {overlap} appear in both values and default. "
                    f"Use values to lock a period or default to make it user-editable, not both."
                )
        super().__init__(label=label, tags=tags, value_format=value_format)
        self._locked_values = dict(values) if values else {}
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

    @property
    def locked_values(self) -> dict:
        """Periods locked with memorized actuals — cannot be overridden at instantiation."""
        return self._locked_values

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
        if self._locked_values:
            parts.append(f"values={self._locked_values!r}")
        if self.has_default:
            parts.append(f"default={self._default!r}")
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"InputLine({', '.join(parts)})"
