from dataclasses import dataclass

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


def _is_values_dict(value_dict: dict) -> bool:
    """
    Check if a dictionary is a valid values dictionary for LineItem.

    A values dictionary contains year:value pairs where:
    - All keys are integers (years)
    - All values are numeric (int/float/bool) or None

    Args:
        value_dict (dict): Dictionary to check

    Returns:
        bool: True if the dictionary is a valid values dictionary, False otherwise

    Examples:
        >>> _is_values_dict({2023: 100, 2024: 200})
        True
        >>> _is_values_dict({2023: 100.5, 2024: None})
        True
        >>> _is_values_dict({2023: True, 2024: False})
        True
        >>> _is_values_dict({"name": "revenue", "category": "income"})
        False
        >>> _is_values_dict({2023: "invalid"})
        False
        >>> _is_values_dict({})
        False
    """
    if not value_dict:
        return False

    try:
        # Use existing validation to check if all keys are integers
        _validate_values_keys(value_dict)

        # Check if all values are numeric (including boolean) or None
        all_values_numeric = all(
            isinstance(val, (int, float, bool)) or val is None
            for val in value_dict.values()
        )

        return all_values_numeric
    except ValueError:
        # If validation fails, it's not a values dictionary
        return False


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
            Defaults to "general" if None is provided.
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
    category: str = None
    label: str = None
    values: dict[int, float | None] = None
    formula: str = None
    value_format: ValueFormat = "no_decimals"

    def __post_init__(self):
        validate_name(self.name)
        _validate_values_keys(self.values)

        # Handle None category by converting to "general"
        if self.category is None:
            self.category = "general"

        # Validate category is a string
        if not isinstance(self.category, str):
            raise TypeError(
                f"LineItem category must be a string, "
                f"got {type(self.category).__name__}"
            )

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
