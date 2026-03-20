"""
InputAssumption class for scalar assumptions provided at model instantiation.

InputAssumption is declared in the model class body like Assumption, but its
value is supplied as a keyword argument when the model is instantiated. An
optional default can be provided for assumptions that are usually stable but
occasionally varied across scenarios.
"""

# Sentinel to distinguish "no default provided" from default=None
_MISSING = object()


class InputAssumption:
    """
    A scalar assumption whose value is provided at model instantiation.

    InputAssumption is declared in the model class body with an optional
    default. Its value is supplied (or overridden) as a keyword argument
    when instantiating the model, making scenario assumptions explicit.

    Unlike Assumption (value baked into the class), InputAssumption values
    vary per model instance — they are the scalar "knobs" of the model.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     # Required input — no default, must be provided every time
        ...     tax_rate = InputAssumption(label="Tax Rate")
        ...
        ...     # Optional input — has a default, can be overridden per scenario
        ...     growth_rate = InputAssumption(default=0.05, label="Growth Rate")
        ...
        ...     revenue = FixedLine(values={2024: 1_000_000})
        ...     after_tax = FormulaLine(
        ...         formula=lambda a, li, t: li.revenue[t] * (1 - a.tax_rate)
        ...     )
        ...
        >>> base = MyModel(periods=[2024], tax_rate=0.21)
        >>> high_tax = MyModel(periods=[2024], tax_rate=0.28)
        >>> custom_growth = MyModel(periods=[2024], tax_rate=0.21, growth_rate=0.08)

    Attributes:
        default: The default value, or absent if no default is set.
        label (str, optional): Human-readable label for display purposes.
        name (str): Set automatically when the class attribute is assigned.
    """

    def __init__(
        self,
        default=_MISSING,
        label: str | None = None,
    ):
        """
        Initialize an InputAssumption.

        Args:
            default: Default scalar value used when none is provided at
                instantiation. Omit to make this assumption required.
            label (str, optional): Human-readable label. Defaults to None.
        """
        self._default = default
        self.label = label
        self.name: str | None = None  # Set by __set_name__

    @property
    def has_default(self) -> bool:
        """True if a default value was provided."""
        return self._default is not _MISSING

    @property
    def default(self):
        """The default value, or raises AttributeError if none was set."""
        if self._default is _MISSING:
            raise AttributeError(
                f"InputAssumption '{self.name}' has no default value."
            )
        return self._default

    def __set_name__(self, owner, name: str):
        """Store the attribute name when assigned to a class."""
        self.name = name

    def __repr__(self):
        """Return a string representation of the InputAssumption."""
        parts = []
        if self.has_default:
            parts.append(f"default={self._default!r}")
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"InputAssumption({', '.join(parts)})"
