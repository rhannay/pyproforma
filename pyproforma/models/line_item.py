from dataclasses import dataclass

from ..constants import ValueFormat
from ._utils import validate_name


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
        category (str): Category or type classification for the line item.
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
    """  # noqa: E501

    name: str
    category: str
    label: str = None
    values: dict[int, float | None] = None
    formula: str = None
    value_format: ValueFormat = "no_decimals"

    def __post_init__(self):
        validate_name(self.name)

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
        """Create LineItem from dictionary."""
        # Convert string keys back to integers for values dict (JSON converts int keys
        # to strings)
        values = item_dict.get("values", {})
        if values:
            values = {int(k): v for k, v in values.items()}

        return cls(
            name=item_dict["name"],
            category=item_dict["category"],
            label=item_dict.get("label"),
            values=values,
            formula=item_dict.get("formula"),
            value_format=item_dict.get("value_format", "no_decimals"),
        )

    def __str__(self):
        if self.values is None:
            values_str = "None"
        else:
            years = sorted(self.values.keys())
            values_str = ", ".join(f"{year}: {self.values[year]}" for year in years)
        return (
            f"LineItem(name='{self.name}', label='{self.label}', "
            f"category='{self.category}', values={{ {values_str} }})"
        )

    def __repr__(self):
        return self.__str__()
