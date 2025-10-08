from typing import TYPE_CHECKING

from .line_item_results import LineItemResults

if TYPE_CHECKING:
    from ..model import Model


class LineItemsResults:
    """
    A helper class that provides convenient methods for exploring and managing
    multiple line items together in a financial model.

    This class is typically instantiated through the Model.line_items() method and
    provides an intuitive interface for batch operations on multiple line items.

    Args:
        model: The parent Model instance
        line_item_names: List of line item names to include

    Examples:
        >>> items_results = model.line_items(['revenue', 'costs', 'profit'])
        >>> print(items_results.names)  # Shows list of line item names
        >>> items_results.set_category('income')  # Sets category for all items
        >>> revenue = items_results.line_item('revenue')  # Get specific item
    """

    def __init__(self, model: "Model", line_item_names: list[str]):
        """
        Initialize LineItemsResults with a model and list of line item names.

        Args:
            model: The parent Model instance
            line_item_names: List of line item names to include

        Raises:
            ValueError: If line_item_names is None, empty, or not a list
            KeyError: If any line item name is not found in the model
        """
        if not isinstance(line_item_names, list):
            raise ValueError("line_item_names must be a list")

        if line_item_names is None or len(line_item_names) == 0:
            raise ValueError("line_item_names must be a non-empty list")

        self.model = model
        self._line_item_names = line_item_names

        # Validate that all line items exist in the model
        available_names = self.model.line_item_names
        for name in line_item_names:
            if name not in available_names:
                raise KeyError(
                    f"Line item '{name}' not found in model. "
                    f"Available line items: {available_names}"
                )

    # ============================================================================
    # INTERNAL/PRIVATE METHODS
    # ============================================================================

    def __str__(self) -> str:
        """
        Return a string representation showing key information about the line items.
        """
        return self.summary()

    def __repr__(self) -> str:
        return f"LineItemsResults(num_items={len(self._line_item_names)})"

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

    # ============================================================================
    # PROPERTY ACCESSORS
    # ============================================================================

    @property
    def names(self) -> list[str]:
        """
        Get the list of line item names included in this results set.

        Returns:
            list[str]: List of line item names
        """
        return self._line_item_names.copy()

    # ============================================================================
    # MODIFICATION METHODS
    # ============================================================================

    def set_category(self, category_name: str) -> None:
        """
        Set the category for all line items in this results set.

        This method updates the category for each line item to the specified
        category_name. The category will be created if it doesn't exist.

        Args:
            category_name (str): The category name to set for all line items

        Raises:
            ValueError: If any line item cannot have its category set (e.g., if it's
                       not a line_item type)

        Examples:
            >>> items = model.line_items(['revenue', 'costs'])
            >>> items.set_category('financials')  # Sets category for both items
        """
        # Build list of updates to apply
        item_updates = []
        for name in self._line_item_names:
            item_updates.append((name, {"category": category_name}))

        # Apply all updates together using the model's batch update method
        self.model.update.update_multiple_line_items(item_updates)

    # ============================================================================
    # ITEM ACCESS METHODS
    # ============================================================================

    def line_item(self, name: str) -> LineItemResults:
        """
        Get a LineItemResults object for a specific line item.

        This method returns a LineItemResults object only if the line item
        was included in the original set of names provided to this LineItemsResults.

        Args:
            name (str): The name of the line item to retrieve

        Returns:
            LineItemResults: Results object for the specified line item

        Raises:
            KeyError: If the line item name was not included in the original set

        Examples:
            >>> items = model.line_items(['revenue', 'costs'])
            >>> revenue = items.line_item('revenue')  # Returns LineItemResults
            >>> profit = items.line_item('profit')  # Raises KeyError
        """
        if name not in self._line_item_names:
            raise KeyError(
                f"Line item '{name}' not found in this LineItemsResults. "
                f"Available items: {self._line_item_names}"
            )

        return LineItemResults(self.model, name)

    def table(self, **kwargs):
        """
        Generate a table containing all line items in this results set.

        This method uses the model's Tables.line_items() method to create a table
        showing all line items included in this LineItemsResults object.

        Args:
            **kwargs: Additional keyword arguments to pass to Tables.line_items().
                     Common options include:
                     - included_cols: List of columns to include (default: ["label"])
                     - group_by_category: Whether to group by category (default: False)
                     - include_percent_change: Whether to include percent change rows
                       (default: False)
                     - hardcoded_color: CSS color for hardcoded values (default: None)

        Returns:
            Table: A Table object containing the line items in this results set

        Examples:
            >>> items = model.line_items(['revenue_sales', 'cost_of_goods'])
            >>> table = items.table()  # Basic table with labels
            >>> table = items.table(group_by_category=True)  # Group by category
            >>> table = items.table(include_percent_change=True)  # With % change
        """
        return self.model.tables.line_items(line_item_names=self.names, **kwargs)

    def total(self, year: int) -> float:
        """
        Calculate the sum of all line items in this results set for a given year.

        This method sums the values of all line items included in this
        LineItemsResults for the specified year. None values are treated as 0.

        Args:
            year (int): The year for which to calculate the total

        Returns:
            float: The sum of all line item values for the specified year

        Raises:
            ValueError: If the year is not in the model's years

        Examples:
            >>> items = model.line_items(['revenue_sales', 'service_revenue'])
            >>> total_revenue = items.total(2024)  # Sum of both revenue items for 2024
            >>> items = model.line_items(['cost_of_goods', 'operating_expenses'])
            >>> total_costs = items.total(2024)  # Sum of both cost items for 2024
        """
        # Validate that the year exists in the model
        if year not in self.model.years:
            raise ValueError(
                f"Year {year} not found in model. Available years: {self.model.years}"
            )

        total = 0.0
        for name in self._line_item_names:
            value = self.model.line_item(name)[year]
            if value is not None:
                total += value

        return total

    def line_items_chart(
        self,
        title: str = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        value_format=None,
    ):
        """
        Create a line chart showing the values of all line items in this results set
        over years.

        This method uses the line item names from this results set and delegates to the
        model's charts.line_items() method.

        Args:
            title (str, optional): Custom chart title. If None, uses default title
                                 "Line Items".
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            value_format (ValueFormat, optional): Y-axis value format. If None, uses the
                                                first item's format.

        Returns:
            Chart figure: The Plotly line chart figure showing all line items

        Raises:
            ValueError: If no line items are found in this results set or if the model
                       has no years defined

        Examples:
            >>> items = model.line_items(['revenue', 'costs'])
            >>> chart = items.line_items_chart()
            >>> chart = items.line_items_chart(title="Revenue vs Costs")
            >>> chart = items.line_items_chart(width=1000, height=600)
        """
        if not self._line_item_names:
            raise ValueError("No line items found in this results set")

        # Use default title if none provided
        if title is None:
            title = "Line Items"

        return self.model.charts.line_items(
            self._line_item_names,
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
        Create a pie chart showing the distribution of line items within this results set for a specific year.

        Args:
            year (int, optional): The year for which to create the pie chart. If None, uses the latest year in the model.
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')

        Returns:
            Chart figure: The Plotly pie chart figure showing the distribution of line items

        Raises:
            ValueError: If no line items are found in this results set or if year is not in model years
        """  # noqa: E501
        if not self._line_item_names:
            raise ValueError("No line items found in this results set")

        return self.model.charts.line_items_pie(
            self._line_item_names,
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
        Return a summary string with key information about the line items.

        Args:
            html (bool, optional): If True, returns HTML formatted output.
                                   Defaults to False.

        Returns:
            str: Formatted summary of the line items
        """
        num_items = len(self._line_item_names)
        items_list = ", ".join(self._line_item_names)

        summary_text = (
            f"LineItemsResults\nNumber of Items: {num_items}\nItems: {items_list}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text
