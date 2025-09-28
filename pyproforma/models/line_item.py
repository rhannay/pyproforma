from __future__ import annotations
from dataclasses import dataclass, field

from ..constants import ValueFormat
from ._utils import validate_name

def _validate_values_keys(values: dict[int, float | None] | None):
    """Validate that all keys in the values dictionary are integers."""
    if values is not None:
        for key in values.keys():
            if not isinstance(key, int):
                raise ValueError(
                    f"Values dictionary key '{key}' must be an integer (year), "
                    f"got {type(key).__name__}"
                )


@dataclass
class LineItem:
    """
    Defines a line item specification for a financial model with values across multiple years.

    A LineItem defines the structure and calculation logic for a line item, storing explicit
    values for specific years or using formulas to calculate values dynamically. Once a
    LineItem is part of a model, the calculated results are available in
    [LineItemResults][pyproforma.models.results.LineItemResults] instances. It's a core
    component of the pyproforma financial modeling system.

    Args:
        name (str): Unique identifier for the line item. Must contain only letters,
            numbers, underscores, or hyphens (no spaces or special characters).
        category (str, optional): Category or type classification for the line item.
            Defaults to "general" if not provided.
        label (str, optional): Human-readable display name. Defaults to name if not provided.
        values (dict[int, float | None], optional): Dictionary mapping years to explicit values.
            Values can be numbers or None. Defaults to empty dict if not provided.
        formula (str, optional): Formula string for calculating values when explicit
            values are not available. Defaults to None.
        value_format (ValueFormat, optional): Format specification for displaying values.
            Must be one of the values in VALUE_FORMATS constant: None, 'str', 'no_decimals',
            'two_decimals', 'percent', 'percent_one_decimal', 'percent_two_decimals'.
            Defaults to 'no_decimals'.

    Raises:
        ValueError: If name contains invalid characters (spaces or special characters).

    Examples:
        >>> # Create a line item with explicit values (including None)
        >>> revenue = LineItem(
        ...     name="revenue",
        ...     category="income",
        ...     label="Total Revenue",
        ...     values={2023: 100000, 2024: None, 2025: 120000}
        ... )

        >>> # Create a line item with a formula
        >>> profit = LineItem(
        ...     name="profit",
        ...     category="income",
        ...     formula="revenue * 0.1"
        ... )

        >>> # Create a line item using default category
        >>> misc_item = LineItem(
        ...     name="misc_expense",
        ...     values={2023: 1000, 2024: 1100}
        ... )
        >>> misc_item.category
        'general'
    """  # noqa: E501

    name: str
    category: str = "general"
    label: str = None
    values: dict[int, float | None] = field(default_factory=dict)
    formula: str = None
    value_format: ValueFormat = "no_decimals"

    def __post_init__(self):
        validate_name(self.name)
        _validate_values_keys(self.values)

    def to_dict(self) -> dict:
        """Convert LineItem to dictionary representation."""
        return {
            "name": self.name,
            "category": self.category,
            "label": self.label,
            "values": self.values,
            "formula": self.formula,
            "value_format": self.value_format,
        }

    @classmethod
    def from_dict(cls, item_dict: dict) -> "LineItem":
        """
        Create LineItem from dictionary.

        Args:
            item_dict (dict): Dictionary containing LineItem properties

        Returns:
            LineItem: New LineItem instance

        Notes:
            If 'category' is missing, None, empty string, or whitespace-only,
            it defaults to "general".
        """
        # Convert string keys back to integers for values dict (JSON converts int keys
        # to strings)
        values = item_dict.get("values", {})
        if values:
            values = {int(k): v for k, v in values.items()}

        return cls(
            name=item_dict["name"],
            category=(item_dict.get("category") or "").strip() or "general",
            label=item_dict.get("label"),
            values=values,
            formula=item_dict.get("formula"),
            value_format=item_dict.get("value_format", "no_decimals"),
        )

    def get_value(self, year) -> float:
        if year not in self.values:
            self.set_value(year)
        return self.values[year]
    
    def set_value(self, year):
        raise NotImplementedError(
            f'Update condition for {self.name} has not been set yet. Use model.define() to define the update condition.'
        )
    
    # DOES NOT CURRENTLY SUPPORT ONE CALLABLE ADDING ANOTHER CALLABLE
    def __add__(self, other: LineItem | float | callable) -> callable:
        def add_expr(year):
            if isinstance(other, (int, float)):
                return self.get_value(year) + other
            elif callable(other):
                return self.get_value(year) + other(year)
            else:
                return self.get_value(year) + other.get_value(year)
        return add_expr
    
    def __sub__(self, other: LineItem | float) -> callable:
        def sub_expr(year):
            if isinstance(other, (int, float)):
                return self.get_value(year) - other
            elif callable(other):
                return self.get_value(year) - other(year)
            else:
                return self.get_value(year) - other.get_value(year)
        return sub_expr

    def __mul__(self, other: LineItem | float) -> callable:
        def mul_expr(year):
            if isinstance(other, (int, float)):
                return self.get_value(year) * other
            elif callable(other):
                return self.get_value(year) * other(year)
            else:
                return self.get_value(year) * other.get_value(year)
        return mul_expr

    def __getitem__(self, key):
        return LaggedLineItem(reference=self, lag=key)
    
    def __setitem__(self, key, value):
        self.values[key] = value

@dataclass
class LaggedLineItem:
    reference: LineItem
    lag: int
    
    def get_value(self, year):
        return self.reference.get_value(year + self.lag)
    
    def __add__(self, other: LineItem | float) -> callable:
        return lambda year: self.reference.__add__(other)(year + self.lag)
    
    def __sub__(self, other: LineItem | float) -> callable:
        return lambda year: self.reference.__sub__(other)(year + self.lag)


    def __mul__(self, other: LineItem | float) -> callable:
        return lambda year: self.reference.__mul__(other)(year + self.lag)

    