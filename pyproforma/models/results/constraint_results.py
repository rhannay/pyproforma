from typing import TYPE_CHECKING

import plotly.graph_objects as go

from pyproforma.tables.table_class import format_value

if TYPE_CHECKING:
    from ..model import Model


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
            ChartGenerationError: If the model has no years defined
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
