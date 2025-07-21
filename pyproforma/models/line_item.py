from typing import List, Union
import pandas as pd
from ._utils import check_name, check_interim_values_by_year
from .formula import calculate_formula
from ..constants import VALUE_FORMATS, ValueFormat


class LineItem:
    """
    Represents a line item in a financial model with values across multiple years.
    
    A LineItem can store explicit values for specific years or use formulas to calculate
    values dynamically. It's a core component of the pyproforma financial modeling system.
    
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
    """
    def __init__(
        self,
        name: str,
        category: str,
        label: str = None,
        values: dict[int, float | None] = None,
        formula: str = None,
        value_format: ValueFormat = 'no_decimals'
    ):

        if not check_name(name):
            raise ValueError("LineItem name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
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
        """
        # Validate interim values by year
        is_valid, error_msg = check_interim_values_by_year(interim_values_by_year)
        if not is_valid:
            raise ValueError(f"Invalid interim values by year: {error_msg}")

        # If interim_values_by_year[year][self.name] already exists, raise an error
        if year in interim_values_by_year and self.name in interim_values_by_year[year]:
            raise ValueError(f"Value for {self.name} in year {year} already exists in interim values.")

        # If value for this year is in .values, return that value (including None)
        if year in self.values:
            return self.values[year]
        
        # No value exists, so use a formula
        if self.formula:
            return calculate_formula(self.formula, interim_values_by_year, year)
        # If no formula is defined, return None
        return None

    def to_dict(self) -> dict:
        """Convert LineItem to dictionary representation."""
        return {
            'name': self.name,
            'category': self.category,
            'label': self.label,
            'values': self.values,
            'formula': self.formula,
            'value_format': self.value_format
        }

    @classmethod
    def from_dict(cls, item_dict: dict) -> 'LineItem':
        """Create LineItem from dictionary."""
        # Convert string keys back to integers for values dict (JSON converts int keys to strings)
        values = item_dict.get('values', {})
        if values:
            values = {int(k): v for k, v in values.items()}
        
        return cls(
            name=item_dict['name'],
            category=item_dict['category'],
            label=item_dict.get('label'),
            values=values,
            formula=item_dict.get('formula'),
            value_format=item_dict.get('value_format', 'no_decimals')
        )



    def __str__(self):
        years = sorted(self.values.keys())
        values_str = ', '.join(f"{year}: {self.values[year]}" for year in years)
        return (f"LineItem(name='{self.name}', label='{self.label}', "
                f"category='{self.category}', values={{ {values_str} }})")

    def __repr__(self):
        return self.__str__()


class Category:
    """
    Represents a category for organizing line items in a financial model.
    
    A Category defines a grouping mechanism for line items and can optionally
    include a total calculation. It's used to organize and structure financial
    statements by grouping related line items together.
    
    Args:
        name (str): Unique identifier for the category. Must contain only letters,
            numbers, underscores, or hyphens (no spaces or special characters).
        label (str, optional): Human-readable display name for the category.
            Defaults to name if not provided.
        include_total (bool, optional): Whether to include a total calculation for
            this category. Defaults to True.
        total_label (str, optional): Label for the total line when include_total is True.
            Defaults to "Total {label}" if not provided.
    
    Attributes:
        name (str): The category's unique identifier.
        label (str): The display name for the category.
        include_total (bool): Whether this category includes a total.
        total_label (str or None): Label for the total line (None if include_total is False).
        total_name (str or None): Name for the total line item (None if include_total is False).
    
    Raises:
        ValueError: If name contains invalid characters (spaces or special characters).
    
    Examples:
        >>> # Create a category with default total
        >>> revenue_cat = Category(
        ...     name="revenue",
        ...     label="Revenue Sources"
        ... )
        >>> print(revenue_cat.total_label)  # "Total Revenue Sources"
        >>> print(revenue_cat.total_name)   # "total_revenue"
        
        >>> # Create a category without total
        >>> notes_cat = Category(
        ...     name="notes",
        ...     label="Notes and Assumptions",
        ...     include_total=False
        ... )
        >>> print(notes_cat.total_label)  # None
        
        >>> # Create a category with custom total label
        >>> expense_cat = Category(
        ...     name="operating_expenses",
        ...     label="Operating Expenses",
        ...     total_label="Total OpEx"
        ... )
    """
    def __init__(self, name: str, label: str = None, include_total: bool = True, total_label: str = None):
        if not check_name(name):
            raise ValueError("Category name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        
        self.name = name
        self.label = label if label is not None else name
        self.include_total = include_total
        
        if include_total:
            self.total_label = total_label if total_label is not None else f"Total {self.label}"
            self.total_name = f"total_{self.name}"
        else:
            self.total_label = None
            self.total_name = None
        
    def __str__(self):
        return f"Category(name='{self.name}', label='{self.label}', total_label='{self.total_label}', total_name='{self.total_name}', include_total={self.include_total})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        """Convert Category to dictionary representation."""
        return {
            'name': self.name,
            'label': self.label,
            'total_label': self.total_label,
            'include_total': self.include_total
        }

    @classmethod
    def from_dict(cls, category_dict: dict) -> 'Category':
        """Create Category from dictionary."""
        return cls(
            name=category_dict['name'],
            label=category_dict.get('label'),
            total_label=category_dict.get('total_label'),
            include_total=category_dict.get('include_total', True)
        )


