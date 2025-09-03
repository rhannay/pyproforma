from typing import TYPE_CHECKING, Optional

import pandas as pd
import plotly.graph_objects as go

from pyproforma.tables.table_class import Table, format_value

if TYPE_CHECKING:
    from .model import Model


class LineItemResults:
    """
    A helper class that provides convenient methods for exploring and analyzing
    a specific named item (line item, assumption, generator, etc.) in a financial model.

    This class is typically instantiated through the Model.item() method and
    provides an intuitive interface for notebook exploration and analysis of individual items.

    Args:
        model: The parent Model instance
        item_name: The name of the item to analyze

    Examples:
        >>> revenue_item = model.line_item('revenue')
        >>> print(revenue_item)  # Shows summary info
        >>> revenue_item.values()  # Returns dict of year: value
        >>> revenue_item.to_series()  # Returns pandas Series
        >>> revenue_item.table()  # Returns Table object
        >>> revenue_item.chart()  # Returns Plotly chart
    """  # noqa: E501

    def __init__(self, model: "Model", item_name: str):
        self.model = model
        self.item_name = item_name
        self._line_item_metadata = model._get_item_metadata(item_name)
        self.source_type = self._line_item_metadata["source_type"]
        self.label = self._line_item_metadata["label"]
        self.value_format = self._line_item_metadata["value_format"]
        if self.source_type == "line_item":
            self._line_item_definition = model.line_item_definition(item_name)
        else:
            self._line_item_definition = None

    def __str__(self) -> str:
        """Return a string representation showing key information about the item."""
        return self.summary()

    def __repr__(self) -> str:
        return (
            f"LineItemResults(item_name='{self.item_name}', "
            f"source_type='{self._line_item_metadata['source_type']}')"
        )

    def values(self) -> dict[int, float]:
        """
        Return a dictionary of year: value for this item.

        Returns:
            dict[int, float]: Dictionary mapping years to item values
        """
        values = {}
        for year in self.model.years:
            values[year] = self.model.value(self.item_name, year)
        return values

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
        return self.model.value(self.item_name, year)

    def is_hardcoded(self, year: int) -> bool:
        """
        Check if the line item has a hardcoded value for a specific year.

        Args:
            year (int): The year to check for hardcoded values

        Returns:
            bool: True if the year has a hardcoded value, False otherwise.
                  Returns False if _line_item_definition is None.
        """
        if self._line_item_definition is None:
            return False
        return self._line_item_definition.is_hardcoded(year)

    def __getitem__(self, year: int) -> float:
        """
        Allow bracket access to item value for a specific year.
        Equivalent to self.value(year).
        """
        return self.value(year)

    def to_series(self) -> pd.Series:
        """
        Return a pandas Series with years as index and values.

        Returns:
            pd.Series: Series with years as index and item values
        """
        values_dict = self.values()
        return pd.Series(values_dict, name=self.item_name)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return a pandas DataFrame with a single row for this item.

        Returns:
            pd.DataFrame: DataFrame with one row containing the item values across years
        """
        values_dict = self.values()
        return pd.DataFrame([values_dict], index=[self.item_name])

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
            self.item_name, include_name=False, hardcoded_color=hardcoded_color
        )

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
            KeyError: If the item name is not found in the model
        """  # noqa: E501
        return self.model.charts.line_item(
            self.item_name,
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
        """
        return self.model.charts.cumulative_percent_change(
            self.item_name, width=width, height=height, template=template
        )

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

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
        current_value = self.model.value(self.item_name, year)
        previous_value = self.model.value(self.item_name, previous_year)

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
        current_value = self.model.value(self.item_name, year)
        base_year_value = self.model.value(self.item_name, base_year)

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
        current_value = self.model.value(self.item_name, year)
        base_year_value = self.model.value(self.item_name, base_year)

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
        current_value = self.model.value(self.item_name, year)
        base_year_value = self.model.value(self.item_name, base_year)

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
            value = self.model.value(self.item_name, year)
            if value is None:
                value = 0  # Treat None values as zero
            cumulative_sum += value

        return cumulative_sum

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
                    value = self.model.value(self.item_name, year)
                    formatted_value = format_value(value, self.value_format)
                    values_list.append(formatted_value)
                value_info = f"\nValues: {', '.join(values_list)}"
            except KeyError:
                value_info = "\nValues: Not available"

        # Get formula information based on source type
        formula_info = ""
        if self.source_type == "line_item":
            try:
                line_item = self.model.line_item_definition(self.item_name)
                if line_item.formula:
                    formula_info = f"\nFormula: {line_item.formula}"
                else:
                    formula_info = "\nFormula: None (explicit values)"
            except KeyError:
                formula_info = "\nFormula: Not available"
        elif self.source_type == "category":
            formula_info = f"\nFormula: Sum of items in category '{self.item_name}'"

        summary_text = (
            f"LineItemResults('{self.item_name}')\n"
            f"Label: {self.label}\n"
            f"Source Type: {self.source_type}\n"
            f"Value Format: {self.value_format}{formula_info}{value_info}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text


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
        self.category_name = category_name
        self.category_metadata = model._get_category_metadata(category_name)
        if self.category_metadata["system_generated"] is False:
            self.category_obj = model.category_definition(category_name)
        else:
            self.category_obj = None
        self.line_item_names = model.line_item_names_by_category(category_name)

    @property
    def name(self) -> str:
        """The category name."""
        return self.category_metadata["name"]

    @property
    def label(self) -> str:
        """The display label for the category."""
        return self.category_metadata["label"]

    @property
    def include_total(self) -> bool:
        """Whether the category includes a total row."""
        return self.category_metadata["include_total"]

    @property
    def total_name(self) -> str:
        """The name used for the category total."""
        return self.category_metadata["total_name"]

    @property
    def total_label(self) -> str:
        """The display label for the category total."""
        return self.category_metadata["total_label"]

    @property
    def system_generated(self) -> bool:
        """Whether the category was auto-generated."""
        return self.category_metadata["system_generated"]

    def __str__(self) -> str:
        """
        Return a string representation showing key information about the category.
        """
        return self.summary()

    def __repr__(self) -> str:
        return (
            f"CategoryResults(category_name='{self.category_name}', "
            f"num_items={len(self.line_item_names)})"
        )

    def totals(self) -> dict[int, float]:
        """
        Return a dictionary of year: total value for this category.

        Returns:
            dict[int, float]: Dictionary mapping years to category totals

        Raises:
            ValueError: If the category doesn't include totals
        """
        if not self.include_total:
            raise ValueError(f"Category '{self.category_name}' does not include totals")

        totals = {}
        for year in self.model.years:
            try:
                totals[year] = self.model.category_total(self.category_name, year)
            except KeyError:
                totals[year] = 0.0

        return totals

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

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return a pandas DataFrame with line items as rows and years as columns.

        Returns:
            pd.DataFrame: DataFrame with line items and their values across years
        """
        values_dict = self.values()

        # Create DataFrame with line items as index and years as columns
        df_data = {}
        for year in self.model.years:
            df_data[year] = [
                values_dict[item_name][year] for item_name in self.line_item_names
            ]

        df = pd.DataFrame(df_data, index=self.line_item_names)

        # Add total row if category includes totals
        if self.include_total:
            try:
                total_row = self.totals()
                df.loc[self.total_name] = [total_row[year] for year in self.model.years]
            except (ValueError, KeyError):
                pass

        return df

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
        return self.model.tables.category(
            self.category_name, hardcoded_color=hardcoded_color
        )

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

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

        # Get totals for all years if category includes totals
        total_info = ""
        if self.include_total and self.model.years:
            try:
                totals_list = []
                for year in self.model.years:
                    total_value = self.model.category_total(self.category_name, year)
                    formatted_total = f"{total_value:,.0f}"
                    totals_list.append(formatted_total)
                total_info = f"\nTotals: {', '.join(totals_list)}"
            except (KeyError, AttributeError):
                total_info = "\nTotals: Not available"

        summary_text = (
            f"CategoryResults('{self.category_name}')\n"
            f"Label: {self.label}\n"
            f"Line Items: {num_items}\n"
            f"Items: {', '.join(item_names)}{total_info}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text


class ConstraintResults:
    """
    A helper class that provides convenient methods for exploring and analyzing
    constraints in a financial model.

    This class is typically instantiated through the Model.constraint() method and
    provides an intuitive interface for notebook exploration and analysis of constraints.

    Args:
        model: The parent Model instance
        constraint_name: The name of the constraint to analyze

    Examples:
        >>> debt_constraint = model.constraint('debt_limit')
        >>> print(debt_constraint)  # Shows summary info
        >>> debt_constraint.values()  # Returns dict of year: value
        >>> debt_constraint.table()  # Returns Table object
        >>> debt_constraint.chart()  # Returns Plotly chart
    """  # noqa: E501

    def __init__(self, model: "Model", constraint_name: str):
        self.model = model
        self.constraint_name = constraint_name
        self.constraint_definition = model.constraint_definition(constraint_name)
        self.line_item_name = self.constraint_definition.line_item_name

        line_item_definition = model.line_item_definition(self.line_item_name)
        self.value_format = line_item_definition.value_format

    def __str__(self) -> str:
        """
        Return a string representation showing key information about the constraint.
        """
        return self.summary()

    def __repr__(self) -> str:
        return f"ConstraintResults(constraint_name='{self.constraint_name}')"

    def line_item_value(self, year: int) -> float:
        """
        Return the line item value for this constraint for a specific year.

        Args:
            year (int): The year to get the line item value for

        Returns:
            float: The line item value for the specified year

        Raises:
            KeyError: If the year is not in the model's years
        """
        return self.model.value(self.line_item_name, year)

    def target(self, year: int) -> float:
        """
        Return the target value for this constraint for a specific year.

        Args:
            year (int): The year to get the target value for

        Returns:
            float: The constraint target value for the specified year

        Raises:
            KeyError: If the year is not in the model's years
        """
        return self.constraint_definition.get_target(year)

    def table(self):
        """
        Return a Table object for this constraint using the tables.constraint() function.

        Returns:
            Table: A Table object containing the constraint formatted for display
        """  # noqa: E501
        return self.model.tables.constraint(self.constraint_name)

    def chart(
        self,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        line_item_type: str = "bar",
        constraint_type: str = "line",
    ) -> go.Figure:
        """
        Create a chart using Plotly showing the values for this constraint over years.

        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')

        Returns:
            go.Figure: The Plotly chart figure

        Raises:
            KeyError: If the constraint name is not found in the model
        """  # noqa: E501
        return self.model.charts.constraint(
            self.constraint_name,
            width=width,
            height=height,
            template=template,
            line_item_type=line_item_type,
            constraint_type=constraint_type,
        )

    def evaluate(self, year: int) -> bool:
        """
        Evaluate whether the constraint is satisfied for a specific year.

        Args:
            year (int): The year to evaluate the constraint for

        Returns:
            bool: True if the constraint is satisfied, False otherwise

        Raises:
            ValueError: If year or line item is not found in the model, or no target available
        """  # noqa: E501
        return self.constraint_definition.evaluate(self.model._value_matrix, year)

    def failing_years(self) -> list[int]:
        """
        Return a list of years where the constraint is not satisfied.

        Returns:
            list[int]: List of years where the constraint fails
        """
        failing = []
        for year in self.model.years:
            try:
                if not self.evaluate(year):
                    failing.append(year)
            except ValueError:
                # Skip years that can't be evaluated
                pass

        return failing

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

    def summary(self, html: bool = False) -> str:
        """
        Return a summary string with key information about the constraint.

        Args:
            html (bool, optional): If True, returns HTML formatted output. Defaults to False.

        Returns:
            str: Formatted summary of the constraint
        """  # noqa: E501
        # Format the target using the line item's value format
        target_info = ""
        try:
            target = self.constraint_definition.target
            operator_symbol = self.constraint_definition.get_operator_symbol()

            if isinstance(target, dict):
                target_str = str(
                    {
                        year: format_value(value, self.value_format)
                        for year, value in target.items()
                    }
                )
                target_info = f"\nTarget: {operator_symbol} {target_str}"
            else:
                formatted_target = format_value(target, self.value_format)
                target_info = f"\nTarget: {operator_symbol} {formatted_target}"
        except (KeyError, AttributeError):
            target_info = "\nTarget: Not available"

        # Get value for first year if available
        value_info = ""
        if self.model.years:
            first_year = self.model.years[0]
            try:
                value = self.model.value(self.line_item_name, first_year)
                formatted_value = format_value(value, self.value_format)
                value_info = f"\nValue ({first_year}): {formatted_value}"
            except KeyError:
                value_info = "\nValue: Not available"

        # Get list of failing years
        failing_years_list = self.failing_years()
        failing_info = ""
        if failing_years_list:
            if html:
                failing_years_str = ", ".join(map(str, failing_years_list))
                failing_info = (
                    f"\n<span style='color: red;'>Failing Years: "
                    f"{failing_years_str}</span>"
                )
            else:
                failing_info = (
                    f"\nFailing Years: {', '.join(map(str, failing_years_list))}"
                )
        else:
            if html:
                failing_info = (
                    "\n<span style='color: green;'>Status: All years pass "
                    "constraint check</span>"
                )
            else:
                failing_info = "\nStatus: All years pass constraint check"

        constraint_label = getattr(
            self.constraint_definition, "label", self.constraint_name
        )
        summary_text = (
            f"ConstraintResults('{self.constraint_name}')\n"
            f"Label: {constraint_label}\n"
            f"Line Item: {self.line_item_name}"
            f"{target_info}{value_info}{failing_info}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text
