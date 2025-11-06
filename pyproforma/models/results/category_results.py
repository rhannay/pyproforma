from typing import TYPE_CHECKING, Optional

import pandas as pd

from pyproforma.tables.table_class import Table

if TYPE_CHECKING:
    from ..model import Model


class CategoryResults:
    """
    A helper class that provides convenient methods for exploring and summarizing
    line items within a specific category of a financial model.

    This class is typically instantiated through the Model.category() method and
    provides an intuitive interface for notebook exploration and analysis.

    Args:
        model: The parent Model instance
        category_name: The name of the category to analyze

    Examples:
        >>> revenue_results = model.category('revenue')
        >>> print(revenue_results)  # Shows summary info
        >>> revenue_results.total()  # Returns dict of year: total
        >>> revenue_results.items  # Returns list of LineItems
        >>> revenue_results.to_dataframe()  # Returns pandas DataFrame
    """

    def __init__(self, model: "Model", category_name: str):
        self.model = model
        self._name = category_name
        # Validate that the category exists by accessing the metadata
        # This will raise a KeyError if the category doesn't exist
        _ = model._get_category_metadata(category_name)

    # ============================================================================
    # INTERNAL/PRIVATE METHODS
    # ============================================================================

    def __str__(self) -> str:
        """
        Return a string representation showing key information about the category.
        """
        return self.summary()

    def __repr__(self) -> str:
        return (
            f"CategoryResults(category_name='{self.name}', "
            f"num_items={len(self.line_item_names)})"
        )

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
    def _category_metadata(self) -> dict:
        """Get the category metadata from the model."""
        return self.model._get_category_metadata(self._name)

    @property
    def name(self) -> str:
        """The category name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name for this category and update it in the model."""
        # Update the category in the model first - if this fails, we don't change
        # local state
        self.model.update.update_category(self._name, new_name=value)
        # Only update local state if model update succeeded
        self._name = value

    @property
    def label(self) -> str:
        """The display label for the category."""
        return self._category_metadata["label"]

    @label.setter
    def label(self, value: str) -> None:
        """Set the label for this category and update it in the model."""
        # Update the category in the model first - if this fails, we don't change
        # local state
        self.model.update.update_category(self._name, label=value)

    @property
    def line_item_names(self) -> list[str]:
        """Get the line item names for this category from the model."""
        return self.model.line_item_names_by_category(self._name)

    @property
    def system_generated(self) -> bool:
        """Whether the category was auto-generated."""
        return self._category_metadata["system_generated"]

    def delete(self, include_line_items: bool = False) -> None:
        """
        Delete this category from the model.

        This method removes the category from the model entirely. After calling this
        method, the CategoryResults object should not be used as the underlying category
        no longer exists.

        The deletion will fail if there are any line items that still reference this
        category, unless include_line_items is True. If include_line_items is True,
        all line items in the category will be deleted first.

        Args:
            include_line_items (bool): If True, delete all line items in this category
                                      before deleting the category. Defaults to False.

        Raises:
            ValueError: If the category cannot be deleted because line items still
                       reference it and include_line_items is False
            KeyError: If the category is not found in the model

        Examples:
            >>> revenue_category = model.category('revenue')
            >>> revenue_category.delete()  # Fails if category has line items
            >>> revenue_category.delete(
            ...     include_line_items=True
            ... )  # Deletes line items first
        """
        # Check if any line items still reference this category
        line_items_in_category = self.line_item_names
        if line_items_in_category and not include_line_items:
            raise ValueError(
                f"Cannot delete category '{self.name}' because it still contains "
                f"line items: {', '.join(line_items_in_category)}. "
                f"Delete or move these line items to other categories first."
            )

        # Delete the category from the model
        # (which will also delete line items if requested)
        self.model.update.delete_category(
            self.name, include_line_items=include_line_items
        )

    # ============================================================================
    # VALUE ACCESS METHODS
    # ============================================================================

    def values(self) -> dict[str, dict[int, float]]:
        """
        Return a nested dictionary of item_name: {year: value} for all items in category.

        Returns:
            dict[str, dict[int, float]]: Nested dictionary with values for each item by year
        """  # noqa: E501
        values = {}
        for item_name in self.line_item_names:
            values[item_name] = {}
            for year in self.model.years:
                try:
                    values[item_name][year] = self.model.value(item_name, year)
                except KeyError:
                    values[item_name][year] = 0.0

        return values

    def total(self, year: int) -> float:
        """
        Calculate the sum of all line items in this category for a given year.

        This method uses the LineItemsResults.total() functionality by getting all
        line items in this category and delegating to their total method. None values
        are treated as 0.

        Args:
            year (int): The year for which to calculate the total

        Returns:
            float: The sum of all line item values in this category for the
                   specified year

        Raises:
            ValueError: If the year is not in the model's years

        Examples:
            >>> revenue_category = model.category('revenue')
            >>> total_revenue = revenue_category.total(2024)  # Sum of all revenue items
            >>> costs_category = model.category('costs')
            >>> total_costs = costs_category.total(2024)  # Sum of all cost items
        """
        # Get all line items in this category
        line_item_names = self.line_item_names

        # If no line items in category, return 0
        if not line_item_names:
            # Still validate the year exists in the model
            if year not in self.model.years:
                raise ValueError(
                    f"Year {year} not found in model. "
                    f"Available years: {self.model.years}"
                )
            return 0.0

        # Use LineItemsResults.total() to calculate the sum
        line_items_results = self.model.line_items(line_item_names)
        return line_items_results.total(year)

    # ============================================================================
    # DATA CONVERSION METHODS
    # ============================================================================

    def to_dataframe(
        self,
        line_item_as_index: bool = True,
        include_label: bool = False,
        include_category: bool = False,
    ) -> pd.DataFrame:
        """
        Return a pandas DataFrame with line items as rows and years as columns.

        This method uses the Model.to_dataframe() method internally, filtering to only
        the line items in this category.

        Args:
            line_item_as_index (bool, optional): If True, use line item names as
                the DataFrame index. If False, include line item names as the
                first column with header 'name'. Defaults to True.
            include_label (bool, optional): If True, add a 'label' column
                containing the display labels for each line item.
                Defaults to False.
            include_category (bool, optional): If True, add a 'category' column
                before the year columns. Defaults to False.

        Returns:
            pd.DataFrame: DataFrame with line items and their values across years.
                Columns depend on parameters:
                - If line_item_as_index=True: Years as columns, line items as
                  index
                - If line_item_as_index=False: 'name' column, then optional
                  label/category columns, then year columns
                - If include_label=True: Adds 'label' column
                - If include_category=True: Adds 'category' column

        Examples:
            >>> revenue_category = model.category('revenue')
            >>>
            >>> # Basic usage - line items as index
            >>> df = revenue_category.to_dataframe()
            >>> # columns: [2023, 2024, 2025]
            >>> # index: ['product_sales', 'service_revenue']
            >>>
            >>> # Line items as column with labels and categories
            >>> df = revenue_category.to_dataframe(
            ...     line_item_as_index=False,
            ...     include_label=True,
            ...     include_category=True
            ... )
            >>> # columns: ['name', 'label', 'category', 2023, 2024, 2025]
        """
        return self.model.to_dataframe(
            line_items=self.line_item_names,
            line_item_as_index=line_item_as_index,
            include_label=include_label,
            include_category=include_category,
        )

    def table(self, hardcoded_color: Optional[str] = None) -> Table:
        """
        Return a Table object for this category using the tables.category() function.

        Args:
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the category items formatted for display
        """  # noqa: E501
        return self.model.tables.category(self.name, hardcoded_color=hardcoded_color)

    def compare_years_table(
        self,
        year1: int,
        year2: int,
        include_change: bool = True,
        include_percent_change: bool = True,
        sort_by: Optional[str] = None,
    ) -> Table:
        """
        Create a comparison table between two years for all line items in this category.

        This method uses the line item names from this category and delegates to the
        model's tables.compare_years() method.

        Args:
            year1 (int): The first year to compare
            year2 (int): The second year to compare
            include_change (bool): Whether to include the Change column.
                                 Defaults to True.
            include_percent_change (bool): Whether to include the Percent Change
                                         column. Defaults to True.
            sort_by (Optional[str]): How to sort the items. Options: None, 'value',
                                   'change', 'percent_change'. None keeps the original
                                   order. Defaults to None.

        Returns:
            Table: A table with columns for year1, year2, and optional change columns
                   for all line items in this category

        Raises:
            ValueError: If year1 or year2 are not in the model's years, or if sort_by
                       is invalid

        Examples:
            >>> revenue_category = model.category('revenue')
            >>> table = revenue_category.compare_years_table(2023, 2024)
            >>> table = revenue_category.compare_years_table(
            ...     2023, 2024, sort_by='change'
            ... )
            >>> table = revenue_category.compare_years_table(
            ...     2023, 2024, include_change=False
            ... )
        """
        return self.model.tables.compare_years(
            year1,
            year2,
            names=self.line_item_names,
            include_change=include_change,
            include_percent_change=include_percent_change,
            sort_by=sort_by,
        )

    def year_over_year_table(
        self,
        year: int,
        include_change: bool = True,
        include_percent_change: bool = True,
        sort_by: Optional[str] = None,
    ) -> Table:
        """
        Create a year-over-year comparison table for all line items in this category.

        This method uses the line item names from this category and delegates to the
        model's tables.year_over_year() method.

        Args:
            year (int): The year to compare (will compare year-1 to year)
            include_change (bool): Whether to include the Change column.
                                 Defaults to True.
            include_percent_change (bool): Whether to include the Percent Change
                                         column. Defaults to True.
            sort_by (Optional[str]): How to sort the items. Options: None, 'value',
                                   'change', 'percent_change'. None keeps the original
                                   order. Defaults to None.

        Returns:
            Table: A table with columns for previous year, current year, and optional
                   change columns for all line items in this category

        Raises:
            ValueError: If year or year-1 are not in the model's years, or if sort_by
                       is invalid

        Examples:
            >>> revenue_category = model.category('revenue')
            >>> table = revenue_category.year_over_year_table(2024)
            >>> table = revenue_category.year_over_year_table(
            ...     2024, sort_by='change'
            ... )
            >>> table = revenue_category.year_over_year_table(
            ...     2024, include_change=False
            ... )
        """
        return self.model.tables.year_over_year(
            year,
            names=self.line_item_names,
            include_change=include_change,
            include_percent_change=include_percent_change,
            sort_by=sort_by,
        )

    def chart(
        self,
        title: str = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        value_format=None,
    ):
        """
        Create a line chart showing the values of all line items in this category
        over years.

        This method uses the line item names from this category and delegates to the
        model's charts.line_items() method.

        Args:
            title (str, optional): Custom chart title. If None, uses default title with
                                 category name.
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            value_format (ValueFormat, optional): Y-axis value format. If None, uses the
                                                first item's format.

        Returns:
            Chart figure: The Plotly line chart figure showing all category line items

        Raises:
            ValueError: If no line items are found in the category or if the model
                       has no years defined

        Examples:
            >>> revenue_category = model.category('revenue')
            >>> chart = revenue_category.chart()
            >>> chart = revenue_category.chart(title="Revenue Trends")
            >>> chart = revenue_category.chart(width=1000, height=600)
        """
        if not self.line_item_names:
            raise ValueError(f"No line items found in category '{self.name}'")

        # Use category label as default title if none provided
        if title is None:
            title = f"{self.label} Line Items"

        return self.model.charts.line_items(
            self.line_item_names,
            title=title,
            width=width,
            height=height,
            template=template,
            value_format=value_format,
        )

    def pie_chart(
        self,
        year: int = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
    ):
        """
        Create a pie chart showing the distribution of line items within this category for a specific year.

        Args:
            year (int, optional): The year for which to create the pie chart. If None, uses the latest year in the model.
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')

        Returns:
            Chart figure: The Plotly pie chart figure showing the distribution of category items

        Raises:
            ValueError: If no line items are found in the category or if year is not in model years
        """  # noqa: E501
        if not self.line_item_names:
            raise ValueError(f"No line items found in category '{self.name}'")

        return self.model.charts.line_items_pie(
            self.line_item_names,
            year,
            width=width,
            height=height,
            template=template,
        )

    # ============================================================================
    # DISPLAY AND SUMMARY METHODS
    # ============================================================================

    def summary(self, html: bool = False) -> str:
        """
        Return a summary string with key statistics about the category.

        Args:
            html (bool, optional): If True, returns HTML formatted output. Defaults to False.

        Returns:
            str: Formatted summary of the category
        """  # noqa: E501
        num_items = len(self.line_item_names)
        item_names = self.line_item_names

        summary_text = (
            f"CategoryResults('{self.name}')\n"
            f"Label: {self.label}\n"
            f"Line Items: {num_items}\n"
            f"Items: {', '.join(item_names)}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text
