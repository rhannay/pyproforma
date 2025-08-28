from ..constants import ValueFormat
from ._utils import check_interim_values_by_year, check_name
from .formula import calculate_formula


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

    def __init__(
        self,
        name: str,
        category: str,
        label: str = None,
        values: dict[int, float | None] = None,
        formula: str = None,
        value_format: ValueFormat = "no_decimals",
    ):
        if not check_name(name):
            raise ValueError(
                (
                    (
                        "LineItem name must only contain letters, numbers, underscores,"
                        " or hyphens (no spaces or special characters)."
                    )
                )
            )
        self.name = name
        self.category = category
        if label is None:
            self.label = name
        else:
            self.label = label
        if values is None:
            self.values = {}
        else:
            self.values = values
        self.formula = formula
        self.value_format = value_format

    def get_value(self, interim_values_by_year: dict, year: int) -> float | None:
        """
        Get the value for this line item in a specific year.

        The method follows this precedence:
        1. Check if value already exists in interim_values_by_year (raises error if found)
        2. Return explicit value from self.values if available for the year (including None)
        3. Calculate value using formula if formula is defined
        4. Return None if no value or formula is available

        Args:
            interim_values_by_year (dict): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
            year (int): The year for which to get the value.

        Returns:
            float or None: The calculated/stored value for the specified year, or None if no value/formula exists.

        Raises:
            ValueError: If value already exists in interim_values_by_year or if interim_values_by_year is invalid.
        """  # noqa: E501
        # Validate interim values by year
        is_valid, error_msg = check_interim_values_by_year(interim_values_by_year)
        if not is_valid:
            raise ValueError(f"Invalid interim values by year: {error_msg}")

        # If interim_values_by_year[year][self.name] already exists, raise an error
        if year in interim_values_by_year and self.name in interim_values_by_year[year]:
            raise ValueError(
                (
                    f"Value for {self.name} in year {year} "
                    "already exists in interim values."
                )
            )

        # If value for this year is in .values, return that value (including None)
        if year in self.values:
            return self.values[year]

        # No value exists, so use a formula
        if self.formula:
            return calculate_formula(self.formula, interim_values_by_year, year)
        # If no formula is defined, return None
        return None

    def is_hardcoded(self, year: int) -> bool:
        """
        Check if the line item has a hardcoded value for a specific year.

        Args:
            year (int): The year to check for hardcoded values.

        Returns:
            bool: True if the year has a hardcoded value in self.values, False otherwise.
        """  # noqa: E501
        return year in self.values

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
        years = sorted(self.values.keys())
        values_str = ", ".join(f"{year}: {self.values[year]}" for year in years)
        return (
            f"LineItem(name='{self.name}', label='{self.label}', "
            f"category='{self.category}', values={{ {values_str} }})"
        )

    def __repr__(self):
        return self.__str__()
