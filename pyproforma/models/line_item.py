from dataclasses import dataclass
from typing import Union

from ..table import Format, NumberFormatSpec
from ._utils import validate_name


def _validate_values_keys(values: dict[int, float | None] | None):
    """Validate that all keys in the values dictionary are integers."""
    if values is not None:
        if not isinstance(values, dict):
            raise TypeError(
                f"LineItem values must be a dictionary or None, "
                f"got {type(values).__name__}"
            )
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
        constant (float, optional): A constant scalar value that applies to all years.
            Cannot be used together with values or formula. Defaults to None.
        value_format (ValueFormat | NumberFormatSpec, optional): Format specification
            for displaying values. Can be a string format like 'no_decimals',
            'two_decimals', 'percent', etc., or a NumberFormatSpec instance for more
            control. Defaults to 'no_decimals'.

    Raises:
        ValueError: If name contains invalid characters (spaces or special characters),
            or if constant is used together with values or formula.

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

        >>> # Create a line item with a constant value
        >>> inflation = LineItem(
        ...     name="inflation_rate",
        ...     category="assumptions",
        ...     constant=0.03
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
    constant: float = None
    value_format: Union[NumberFormatSpec, dict, None] = Format.NO_DECIMALS

    def __post_init__(self):
        validate_name(self.name)
        _validate_values_keys(self.values)

        # Validate that constant is not used with values or formula
        if self.constant is not None:
            if self.values is not None:
                raise ValueError(
                    f"LineItem '{self.name}' cannot have both 'constant' and "
                    f"'values'. Use either constant for a scalar value or values "
                    f"for year-specific values."
                )
            if self.formula is not None:
                raise ValueError(
                    f"LineItem '{self.name}' cannot have both 'constant' and "
                    f"'formula'. Use either constant for a scalar value or "
                    f"formula for calculated values."
                )
            # Validate that constant is numeric
            if not isinstance(self.constant, (int, float, bool)):
                raise TypeError(
                    f"LineItem constant must be numeric (int, float, or bool), "
                    f"got {type(self.constant).__name__}"
                )

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
        # Serialize value_format
        if isinstance(self.value_format, NumberFormatSpec):
            value_format_serialized = self.value_format.to_dict()
        else:
            value_format_serialized = self.value_format

        return {
            "name": self.name,
            "category": self.category,
            "label": self.label,
            "values": self.values,
            "formula": self.formula,
            "constant": self.constant,
            "value_format": value_format_serialized,
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
        values = item_dict.get("values")
        if values:
            values = {int(k): v for k, v in values.items()}

        # Deserialize value_format
        value_format_raw = item_dict.get("value_format", Format.NO_DECIMALS)
        if isinstance(value_format_raw, dict):
            value_format = NumberFormatSpec.from_dict(value_format_raw)
        else:
            value_format = value_format_raw

        return cls(
            name=item_dict["name"],
            category=(item_dict.get("category") or "").strip() or "general",
            label=item_dict.get("label"),
            values=values,
            formula=item_dict.get("formula"),
            constant=item_dict.get("constant"),
            value_format=value_format,
        )
