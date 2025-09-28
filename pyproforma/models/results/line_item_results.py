from typing import TYPE_CHECKING, Optional

import pandas as pd
import plotly.graph_objects as go

from pyproforma.constants import ValueFormat
from pyproforma.tables.table_class import Table, format_value

if TYPE_CHECKING:
    from ..model import Model


class LineItemResults:
    """
    A helper class that provides convenient methods for exploring and analyzing
    a specific named item (line item, assumption, generator, etc.) in a financial model.

    This class is typically instantiated through the Model.item() method and
    provides an intuitive interface for notebook exploration and analysis of individual items.

    The class supports bracket notation for both getting and setting values by year:
    - Use `item[year]` to get the value for a specific year
    - Use `item[year] = value` to set a hardcoded value for a specific year

    Args:
        model: The parent Model instance
        item_name: The name of the item to analyze

    Examples:
        >>> revenue_item = model.line_item('revenue')
        >>> print(revenue_item)  # Shows summary info
        >>> revenue_item.values  # Returns dict of year: value
        >>> revenue_item[2024]  # Get value for 2024 using bracket notation
        >>> revenue_item[2025] = 150  # Set hardcoded value for 2025 using bracket notation
        >>> revenue_item.to_series()  # Returns pandas Series
        >>> revenue_item.table()  # Returns Table object
        >>> revenue_item.chart()  # Returns Plotly chart
    """  # noqa: E501

    def __init__(self, model: "Model", item_name: str):
        self.model = model
        self._name = item_name

        # Validate that item_name exists in the model by attempting to get its metadata
        # This will raise a KeyError if the item doesn't exist
        try:
            _ = self._line_item_metadata
        except KeyError:
            raise KeyError(f"Item '{item_name}' not found in model")

    # ============================================================================
    # INTERNAL/PRIVATE METHODS
    # ============================================================================

    def __str__(self) -> str:
        """Return a string representation showing key information about the item."""
        return self.summary()

    def __repr__(self) -> str:
        return f"LineItemResults(name='{self.name}', source_type='{self.source_type}')"

    def __getitem__(self, year: int) -> float:
        """
        Allow bracket access to item value for a specific year.
        Equivalent to self.value(year).
        """
        return self.value(year)

    def __setitem__(self, year: int, value: float) -> None:
        """
        Allow bracket assignment to set item value for a specific year.
        Equivalent to self.set_value(year, value).

        Args:
            year (int): The year to set the value for
            value (float): The value to set
        """
        self.set_value(year, value)

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

    # ============================================================================
    # PROPERTY ACCESSORS (GETTERS AND SETTERS)
    # ============================================================================

    @property
    def _line_item_metadata(self) -> dict:
        """Get the metadata for this line item from the model."""
        return self.model._get_item_metadata(self._name)

    @property
    def source_type(self) -> str:
        """Get the source type for this line item."""
        return self._line_item_metadata["source_type"]

    @property
    def hardcoded_values(self) -> dict | None:
        """Get the hardcoded values for this line item."""
        return self._line_item_metadata["hardcoded_values"]

    @property
    def name(self) -> str:
        """Get the name of this line item."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set name on {self.source_type} item '{self.name}'. "
                f"Only line_item types support name modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, new_name=value)
        # Only update local state if model update succeeded
        self._name = value

    @property
    def label(self) -> str:
        """Get the label for this line item."""
        return self._line_item_metadata["label"]

    @label.setter
    def label(self, value: str) -> None:
        """Set the label for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set label on {self.source_type} item '{self.name}'. "
                f"Only line_item types support label modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, label=value)

    @property
    def formula(self) -> str | None:
        """Get the formula for this line item."""
        return self._line_item_metadata["formula"]

    @formula.setter
    def formula(self, value: str | None) -> None:
        """Set the formula for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set formula on {self.source_type} item '{self.name}'. "
                f"Only line_item types support formula modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, formula=value)

    @property
    def value_format(self) -> ValueFormat:
        """Get the value format for this line item."""
        return self._line_item_metadata["value_format"]

    @value_format.setter
    def value_format(self, value: ValueFormat) -> None:
        """Set the value format for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set value_format on {self.source_type} item '{self.name}'. "
                f"Only line_item types support value_format modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, value_format=value)

    @property
    def category(self) -> str:
        """Get the category for this line item."""
        return self._line_item_metadata["category"]

    @category.setter
    def category(self, value: str) -> None:
        """Set the category for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set category on {self.source_type} item '{self.name}'. "
                f"Only line_item types support category modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, category=value)

    def delete(self) -> None:
        """
        Delete this line item from the model.

        This method removes the line item from the model entirely. After calling this
        method, the LineItemResults object should not be used as the underlying line
        item no longer exists.

        Raises:
            ValueError: If the item cannot be deleted (validation fails) or if this is
                       not a line_item type (only line_item types can be deleted)
            KeyError: If the line item is not found in the model

        Examples:
            >>> revenue_item = model.line_item('revenue')
            >>> revenue_item.delete()  # Removes 'revenue' line item from the model
        """
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot delete {self.source_type} item '{self.name}'. "
                f"Only line_item types support deletion."
            )

        # Delete the line item from the model
        self.model.update.delete_line_item(self.name)

    # ============================================================================
    # VALUE ACCESS METHODS
    # ============================================================================

    @property
    def values(self) -> dict[int, float]:
        """
        Return a dictionary of year: value for this item.

        Returns:
            dict[int, float]: Dictionary mapping years to item values
        """
        values = {}
        for year in self.model.years:
            values[year] = self.model.value(self.name, year)
        return values

    @values.setter
    def values(self, value: dict[int, float]) -> None:
        """Set the values for this line item and update it in the model."""
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set values on {self.source_type} item '{self.name}'. "
                f"Only line_item types support values modification."
            )
        # Update the line item in the model first - if this fails, we don't change
        # local state
        self.model.update.update_line_item(self.name, values=value)

    def value(self, year: int) -> float:
        """
        Return the value for this item for a specific year.

        Args:
            year (int): The year to get the value for

        Returns:
            float: The item value for the specified year

        Raises:
            KeyError: If the year is not in the model's years
        """
        return self.model.value(self.name, year)

    def is_hardcoded(self, year: int) -> bool:
        """
        Check if the line item has a hardcoded value for a specific year.

        Args:
            year (int): The year to check for hardcoded values

        Returns:
            bool: True if the year has a hardcoded value, False otherwise.
                  Returns False if hardcoded_values is None or empty.
        """
        if self.hardcoded_values is None:
            return False
        return year in self.hardcoded_values

    def set_value(self, year: int, value: float) -> None:
        """
        Set the value for this item for a specific year as a hardcoded value.

        This method sets a hardcoded value for the specified year, which will
        override any formula calculation for that year.

        Args:
            year (int): The year to set the value for
            value (float): The value to set

        Raises:
            ValueError: If this is not a line_item type (only line_item types support
                       value modification)
            KeyError: If the year is not in the model's years

        Examples:
            >>> revenue_item = model.line_item('revenue')
            >>> revenue_item.set_value(2024, 99)  # Sets hardcoded value for 2024
            >>> revenue_item[2025] = 150  # Alternative bracket syntax
        """
        if self.source_type != "line_item":
            raise ValueError(
                f"Cannot set value on {self.source_type} item '{self.name}'. "
                f"Only line_item types support value modification."
            )

        if year not in self.model.years:
            raise KeyError(f"Year {year} not found in model years: {self.model.years}")

        # Get current values from the line item definition
        current_values = self.hardcoded_values

        # Add/update the value for this year
        updated_values = {**current_values, year: value}

        # Update the line item in the model
        self.model.update.update_line_item(self.name, values=updated_values)

    # ============================================================================
    # ANALYSIS AND CALCULATION METHODS
    # ============================================================================

    def percent_change(self, year: int) -> float:
        """
        Calculate the percent change of this line item from the previous year to the given year.

        Args:
            year (int): The year to calculate percent change for

        Returns:
            float: The percent change as a decimal (e.g., 0.1 for 10% increase)
                   None if calculation is not possible (first year, zero previous value, or None values)

        Raises:
            KeyError: If the year is not found in the model
        """  # noqa: E501
        # Check if this is the first year
        if year == self.model.years[0]:
            return None

        # Get the index of the current year to find the previous year
        try:
            year_index = self.model.years.index(year)
        except ValueError:
            raise KeyError(f"Year {year} not found in model years: {self.model.years}")

        previous_year = self.model.years[year_index - 1]

        # Get values for current and previous years
        current_value = self[year]
        previous_value = self[previous_year]

        # Handle None values or zero previous value
        if previous_value is None or current_value is None:
            return None
        if previous_value == 0:
            return None

        # Calculate percent change: (current - previous) / previous
        return (current_value - previous_value) / previous_value

    def cumulative_percent_change(self, year: int, start_year: int = None) -> float:
        """
        Calculate the cumulative percent change of this item from a base year to the given year.

        Args:
            year (int): The year to calculate cumulative change for
            start_year (int, optional): The base year for calculation. If None, uses the first year in the model.

        Returns:
            float: The cumulative percent change as a decimal (e.g., 0.1 for 10% increase)
                   None if calculation is not possible (same as start year, zero start year value, or None values)

        Raises:
            KeyError: If the year or start_year is not found in the model
        """  # noqa: E501
        # Determine the base year
        base_year = start_year if start_year is not None else self.model.years[0]

        # Validate years exist
        if year not in self.model.years:
            raise KeyError(f"Year {year} not found in model years: {self.model.years}")
        if base_year not in self.model.years:
            raise KeyError(
                f"Start year {base_year} not found in model years: {self.model.years}"
            )

        # Check if this is the same as the base year
        if year == base_year:
            return 0

        # Get values for current and base years
        current_value = self[year]
        base_year_value = self[base_year]

        # Handle None values or zero base year value
        if base_year_value is None or current_value is None:
            return None
        if base_year_value == 0:
            return None

        # Calculate percent change: (current - base) / base
        return (current_value - base_year_value) / base_year_value

    def cumulative_change(self, year: int, start_year: int = None) -> float:
        """
        Calculate the cumulative absolute change of this item from a base year to the given year.

        Args:
            year (int): The year to calculate cumulative change for
            start_year (int, optional): The base year for calculation. If None, uses the first year in the model.

        Returns:
            float: The cumulative absolute change (current value - base year value)
                   None if calculation is not possible (same as start year or None values)

        Raises:
            KeyError: If the year or start_year is not found in the model
        """  # noqa: E501
        # Determine the base year
        base_year = start_year if start_year is not None else self.model.years[0]

        # Validate years exist
        if year not in self.model.years:
            raise KeyError(f"Year {year} not found in model years: {self.model.years}")
        if base_year not in self.model.years:
            raise KeyError(
                f"Start year {base_year} not found in model years: {self.model.years}"
            )

        # Get values for current and base years
        current_value = self[year]
        base_year_value = self[base_year]

        # Handle None values
        if base_year_value is None or current_value is None:
            return None

        # Check if this is the same as the base year
        if year == base_year:
            return 0

        # Calculate absolute change: current - base
        return current_value - base_year_value

    def index_to_year(self, year: int, start_year: int = None) -> float:
        """
        Calculate an indexed value where the start year is set to 100 and other years are indexed from there.

        Args:
            year (int): The year to calculate indexed value for
            start_year (int, optional): The base year for indexing. If None, uses the first year in the model.

        Returns:
            float: The indexed value (e.g., 110 for 10% increase from base year, 90 for 10% decrease)
                   100 if same as start year
                   None if calculation is not possible (zero start year value or None values)

        Raises:
            KeyError: If the year or start_year is not found in the model
        """  # noqa: E501
        # Determine the base year
        base_year = start_year if start_year is not None else self.model.years[0]

        # Validate years exist
        if year not in self.model.years:
            raise KeyError(f"Year {year} not found in model years: {self.model.years}")
        if base_year not in self.model.years:
            raise KeyError(
                f"Start year {base_year} not found in model years: {self.model.years}"
            )

        # Get values for current and base years
        current_value = self[year]
        base_year_value = self[base_year]

        # Handle None values or zero base year value
        if base_year_value is None or current_value is None:
            return None
        if base_year_value == 0:
            return None

        # Calculate indexed value: (current / base) * 100
        return (current_value / base_year_value) * 100.0

    def cumulative(self, years: Optional[list[int]] = None) -> float:
        """
        Calculate the cumulative sum of this item's values for the specified years.

        Args:
            years (list[int], optional): List of years to sum. If None, uses all years in the model.

        Returns:
            float: The cumulative sum of values for the specified years. None values are treated as zero.

        Raises:
            KeyError: If any year in the years list is not found in the model
        """  # noqa: E501
        # Use all years if none specified
        years_to_sum = years if years is not None else self.model.years

        # Validate all years exist in the model
        for year in years_to_sum:
            if year not in self.model.years:
                raise KeyError(
                    f"Year {year} not found in model years: {self.model.years}"
                )

        # Sum values for all specified years
        cumulative_sum = 0
        for year in years_to_sum:
            value = self[year]
            if value is None:
                value = 0  # Treat None values as zero
            cumulative_sum += value

        return cumulative_sum

    # ============================================================================
    # DATA CONVERSION METHODS
    # ============================================================================

    def to_series(self) -> pd.Series:
        """
        Return a pandas Series with years as index and values.

        Returns:
            pd.Series: Series with years as index and item values
        """
        values_dict = self.values
        return pd.Series(values_dict, name=self.name)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return a pandas DataFrame with a single row for this item.

        Returns:
            pd.DataFrame: DataFrame with one row containing the item values across years
        """
        values_dict = self.values
        return pd.DataFrame([values_dict], index=[self.name])

    def table(self, hardcoded_color: Optional[str] = None) -> Table:
        """
        Return a Table object for this item using the tables.line_item() function.

        Args:
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the item formatted for display
        """  # noqa: E501
        return self.model.tables.line_item(
            self.name, include_name=False, hardcoded_color=hardcoded_color
        )

    # ============================================================================
    # VISUALIZATION METHODS
    # ============================================================================

    def chart(
        self,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        chart_type: str = "line",
    ) -> go.Figure:
        """
        Create a chart using Plotly showing the values for this item over years.

        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')

        Returns:
            go.Figure: The Plotly chart figure

        Raises:
            ChartGenerationError: If the model has no years defined
            KeyError: If the item name is not found in the model
        """  # noqa: E501
        return self.model.charts.line_item(
            self.name,
            width=width,
            height=height,
            template=template,
            chart_type=chart_type,
        )

    def cumulative_percent_change_chart(
        self, width: int = 800, height: int = 600, template: str = "plotly_white"
    ) -> go.Figure:
        """
        Create a chart showing cumulative percentage change from a base year.

        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')

        Returns:
            go.Figure: The Plotly chart figure showing cumulative change percentages

        Raises:
            ChartGenerationError: If the model has no years defined
        """
        return self.model.charts.cumulative_percent_change(
            self.name, width=width, height=height, template=template
        )

    # ============================================================================
    # DISPLAY AND SUMMARY METHODS
    # ============================================================================

    def summary(self, html: bool = False) -> str:
        """
        Return a summary string with key information about the line item.

        Args:
            html (bool, optional): If True, returns HTML formatted output. Defaults to False.

        Returns:
            str: Formatted summary of the line item
        """  # noqa: E501
        # Get values for all years as a list
        value_info = ""
        if self.model.years:
            try:
                values_list = []
                for year in self.model.years:
                    value = self.model.value(self.name, year)
                    formatted_value = format_value(value, self.value_format)
                    values_list.append(formatted_value)
                value_info = f"\nValues: {', '.join(values_list)}"
            except KeyError:
                value_info = "\nValues: Not available"

        # Get formula information based on source type
        formula_info = ""
        if self.source_type == "category":
            formula_info = f"\nFormula: Sum of items in category '{self.name}'"
        elif self.formula:
            formula_info = f"\nFormula: {self.formula}"
        else:
            formula_info = "\nFormula: None (explicit values)"

        summary_text = (
            f"LineItemResults('{self.name}')\n"
            f"Label: {self.label}\n"
            f"Source Type: {self.source_type}\n"
            f"Category: {self.category}\n"
            f"Value Format: {self.value_format}{formula_info}{value_info}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text
