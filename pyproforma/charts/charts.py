from typing import TYPE_CHECKING, Union

import plotly.graph_objects as go

from ..constants import ValueFormat
from .chart_class import Chart, ChartDataSet

if TYPE_CHECKING:
    from pyproforma import Model


class ChartGenerationError(Exception):
    """Exception raised when a chart cannot be generated."""

    pass


class Charts:
    """Charts namespace for a PyProforma model.

    Charts is the namespace for chart functions for a PyProforma model. It provides
    various methods to create interactive Plotly charts from model data, including
    line charts, bar charts, pie charts, and specialized charts for financial analysis
    like cumulative changes and indexed values. All charts are generated using Plotly
    and return Plotly Figure objects for display in Jupyter notebooks or web applications.
    """  # noqa: E501

    def __init__(self, model: "Model"):
        """Initialize the Charts namespace with a PyProforma model.

        Args:
            model (Model): The PyProforma model instance to create charts from.
        """
        self._model = model

    def line_item(
        self,
        name: str,
        title: str = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        chart_type: str = "line",
    ) -> go.Figure:
        """
        Create a chart using Plotly showing the values for a given name over years.

        Args:
            name (str): The name of the item to chart (line item, assumption, etc.)
            title (str, optional): Custom chart title. If None, uses default title "{label}".
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')

        Returns:
            Chart figure: The Plotly chart figure

        Raises:
            ChartGenerationError: If the model has no years defined
            KeyError: If the name is not found in the model
        """  # noqa: E501
        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get the item info and label for display
        try:
            label = self._model.line_item(name).label
            value_format = self._model.line_item(name).value_format
        except KeyError:
            raise KeyError(f"Name '{name}' not found in model defined names.")

        # Get values for all years
        years = self._model.years
        values = []
        for year in years:
            try:
                value = self._model.value(name, year)
                values.append(value)
            except KeyError:
                values.append(0.0)

        # Create dataset
        dataset = ChartDataSet(label=label, data=values, color="blue", type=chart_type)

        # Create chart configuration
        chart_title = title if title is not None else f"{label}"
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=[dataset],
            title=chart_title,
            value_format=value_format,
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig

    def line_items(
        self,
        item_names: list[str],
        title: str = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        value_format: ValueFormat = None,
    ) -> go.Figure:
        """
        Create a line chart using Plotly showing the values for multiple items over years.

        Args:
            item_names (list[str]): List of item names to chart (line items, assumptions, etc.)
            title (str, optional): Custom chart title. If None, uses default title "Multiple Line Items".
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            value_format (ValueFormat, optional): Y-axis value format. If None, uses the first item's format.

        Returns:
            Chart figure: The Plotly chart figure with multiple lines

        Raises:
            ValueError: If item_names list is empty or if the model has no years defined
            KeyError: If any name is not found in the model
        """  # noqa: E501
        if not item_names:
            raise ValueError("item_names list cannot be empty")

        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get years once for all items
        years = self._model.years
        datasets = []

        # Get value_format from the parameter or first item
        if value_format is None:
            try:
                value_format = self._model.line_item(item_names[0]).value_format
            except KeyError:
                raise KeyError(
                    f"Name '{item_names[0]}' not found in model defined names."
                )

        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.line_item(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")

            # Get values for all years
            values = []
            for year in years:
                try:
                    value = self._model.value(name, year)
                    values.append(value)
                except KeyError:
                    values.append(0.0)

            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=label,
                data=values,
                # color=colors[i % len(colors)],
                type="line",
            )
            datasets.append(dataset)

        # Create chart configuration
        chart_title = title if title is not None else "Multiple Line Items"
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=chart_title,
            value_format=value_format,
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig

    def cumulative_percent_change(
        self,
        item_names: Union[str, list[str]],
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        start_year: int = None,
    ) -> go.Figure:
        """
        Create a line chart using Plotly showing the cumulative percent change for one or more items over years.

        Args:
            item_names (str or list[str]): Single item name or list of item names to chart cumulative percent change for
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            start_year (int, optional): The base year for calculation. If None, uses the first year in the model.

        Returns:
            Chart figure: The Plotly chart figure showing cumulative percent change

        Raises:
            ValueError: If item_names is empty
            ChartGenerationError: If the model has no years defined
            KeyError: If any name is not found in the model
        """  # noqa: E501
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]

        if not item_names:
            raise ValueError("item_names cannot be empty")

        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get years once for all items
        years = self._model.years
        datasets = []

        # Define colors for multiple lines (cycles through if more items than colors)
        colors = [
            "blue",
            "red",
            "green",
            "orange",
            "purple",
            "brown",
            "pink",
            "gray",
            "olive",
            "cyan",
        ]

        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.line_item(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")

            # Get cumulative percent change values for all years
            values = []
            for year in years:
                try:
                    cum_pct_change = self._model.line_item(
                        name
                    ).cumulative_percent_change(year, start_year=start_year)
                    # Convert to percentage (multiply by 100)
                    # for better chart readability
                    if cum_pct_change is not None:
                        values.append(cum_pct_change)
                    else:
                        values.append(
                            0.0
                        )  # First year or when calculation not possible
                except (KeyError, ValueError) as e:
                    # Re-raise the error with context
                    raise e

            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=f"{label} Cumulative % Change",
                data=values,
                color=colors[i % len(colors)],
                type="line",
            )
            datasets.append(dataset)

        # Create chart configuration
        chart_title = "Cumulative Percent Change Over Time"
        if len(item_names) == 1:
            chart_title = f"{datasets[0].label}"

        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=chart_title,
            value_format="percent",
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig

    def cumulative_change(
        self,
        item_names: Union[str, list[str]],
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        start_year: int = None,
    ) -> go.Figure:
        """
        Create a line chart using Plotly showing the cumulative absolute change for one or more items over years.

        Args:
            item_names (str or list[str]): Single item name or list of item names to chart cumulative change for
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            start_year (int, optional): The base year for calculation. If None, uses the first year in the model.

        Returns:
            Chart figure: The Plotly chart figure showing cumulative absolute change

        Raises:
            ValueError: If item_names is empty
            ChartGenerationError: If the model has no years defined
            KeyError: If any name is not found in the model
        """  # noqa: E501
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]

        if not item_names:
            raise ValueError("item_names cannot be empty")

        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get years once for all items
        years = self._model.years
        datasets = []

        # Define colors for multiple lines (cycles through if more items than colors)
        colors = [
            "blue",
            "red",
            "green",
            "orange",
            "purple",
            "brown",
            "pink",
            "gray",
            "olive",
            "cyan",
        ]

        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.line_item(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")

            # Get cumulative change values for all years
            values = []
            for year in years:
                try:
                    cum_change = self._model.line_item(name).cumulative_change(
                        year,
                        start_year=start_year,
                    )
                    # Handle None values (like first year or when
                    # calculation not possible)
                    if cum_change is not None:
                        values.append(cum_change)
                    else:
                        values.append(
                            0.0
                        )  # First year or when calculation not possible
                except (KeyError, ValueError) as e:
                    # Re-raise the error with context
                    raise e

            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=f"{label} Cumulative Change",
                data=values,
                color=colors[i % len(colors)],
                type="line",
            )
            datasets.append(dataset)

        # Create chart configuration
        chart_title = "Cumulative Change Over Time"
        if len(item_names) == 1:
            chart_title = f"{datasets[0].label}"

        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=chart_title,
            value_format="currency",
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig

    def index_to_year(
        self,
        item_names: Union[str, list[str]],
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        start_year: int = None,
    ) -> go.Figure:
        """
        Create a line chart using Plotly showing the indexed values for one or more items over years.

        The start year is set to 100 and other years are indexed from there.

        Args:
            item_names (str or list[str]): Single item name or list of item names to chart indexed values for
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            start_year (int, optional): The base year for indexing. If None, uses the first year in the model.

        Returns:
            Chart figure: The Plotly chart figure showing indexed values

        Raises:
            ValueError: If item_names is empty
            ChartGenerationError: If the model has no years defined
            KeyError: If any name is not found in the model
        """  # noqa: E501
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]

        if not item_names:
            raise ValueError("item_names cannot be empty")

        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get years once for all items
        years = self._model.years
        datasets = []

        # Define colors for multiple lines (cycles through if more items than colors)
        colors = [
            "blue",
            "red",
            "green",
            "orange",
            "purple",
            "brown",
            "pink",
            "gray",
            "olive",
            "cyan",
        ]

        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.line_item(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")

            # Get indexed values for all years
            values = []
            for year in years:
                try:
                    indexed_value = self._model.line_item(name).index_to_year(
                        year, start_year=start_year
                    )
                    # Handle None values (like when base year is zero or None values)
                    if indexed_value is not None:
                        values.append(indexed_value)
                    else:
                        values.append(None)  # When calculation not possible
                except (KeyError, ValueError) as e:
                    # Re-raise the error with context
                    raise e

            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=f"{label} Index",
                data=values,
                color=colors[i % len(colors)],
                type="line",
            )
            datasets.append(dataset)

        # Create chart configuration
        chart_title = "Index to Year Over Time"
        if len(item_names) == 1:
            chart_title = f"{datasets[0].label}"

        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=chart_title,
            value_format="number",
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig

    def line_items_pie(
        self,
        item_names: list[str],
        year: int = None,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
    ) -> go.Figure:
        """
        Create a pie chart using Plotly showing the values for multiple line items at a specific year.

        Args:
            item_names (list[str]): List of line item names to include in the pie chart
            year (int, optional): The year for which to create the pie chart. If None, uses the latest year in the model.
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')

        Returns:
            Chart figure: The Plotly pie chart figure

        Raises:
            ValueError: If item_names list is empty, if the model has no years defined, or if year is not in model years
            KeyError: If any name is not found in the model
        """  # noqa: E501
        if not item_names:
            raise ValueError("item_names list cannot be empty")

        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # If year is None, use the latest year in the model
        years = self._model.years
        if year is None:
            year = max(years)

        # Validate year is in model years
        if year not in years:
            raise ValueError(f"Year {year} not found in model years: {years}")

        # Get values and labels for the specified year
        values = []
        labels = []

        # Get value_format from the first item (assuming all items have similar format)
        try:
            value_format = self._model.line_item(item_names[0]).value_format
        except KeyError:
            raise KeyError(f"Name '{item_names[0]}' not found in model defined names.")

        for name in item_names:
            # Get the item info and label for display
            try:
                label = self._model.line_item(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")

            # Get value for the specified year
            try:
                value = self._model.value(name, year)
                # Only include positive values in pie chart
                if value > 0:
                    values.append(value)
                    labels.append(label)
            except KeyError:
                # Skip items that don't have values for this year
                continue

        if not values:
            raise ValueError(
                f"No positive values found for the specified items in year {year}"
            )

        # Create pie chart dataset
        dataset = ChartDataSet(
            label=f"Line Items Distribution ({year})", data=values, type="pie"
        )

        # Create chart configuration
        chart = Chart(
            labels=labels,
            data_sets=[dataset],
            title=f"Line Items Distribution - {year}",
            value_format=value_format,
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, height=height, template=template, show_legend=False
        )

        return fig

    def constraint(
        self,
        constraint_name: str,
        width: int = 800,
        height: int = 600,
        template: str = "plotly_white",
        line_item_type: str = "bar",
        constraint_type: str = "line",
    ) -> go.Figure:
        """
        Create a chart using Plotly showing both the line item values and constraint target values over years.

        Args:
            constraint_name (str): The name of the constraint to chart
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            line_item_type (str): Type of chart for line item data - 'line', 'bar', etc. (default: 'line')
            constraint_type (str): Type of chart for constraint target data - 'line', 'bar', etc. (default: 'bar')

        Returns:
            Chart figure: The Plotly chart figure with both datasets

        Raises:
            ChartGenerationError: If the model has no years defined
            KeyError: If the constraint name is not found in the model
        """  # noqa: E501
        # Check if years are defined
        if not self._model.years:
            raise ChartGenerationError(
                "Cannot create chart: model has no years defined. "
                "Please add years to the model before creating charts."
            )

        # Get the constraint
        try:
            constraint_results = self._model.constraint(constraint_name)
        except KeyError:
            raise KeyError(
                f"Constraint '{constraint_name}' not found in model constraints."
            )

        # Get the associated line item info
        line_item_name = constraint_results.line_item_name
        try:
            line_item = self._model.line_item(line_item_name)
            line_item_label = line_item.label
            value_format = line_item.value_format
        except KeyError:
            raise KeyError(
                f"Line item '{line_item_name}' not found in model defined names."
            )

        # Get years
        years = self._model.years

        # Get line item values for all years
        line_item_values = []
        for year in years:
            try:
                value = self._model.value(line_item_name, year)
                line_item_values.append(value)
            except KeyError:
                line_item_values.append(0.0)

        # Get constraint target values for all years
        constraint_values = []
        for year in years:
            target_value = constraint_results.target_by_year(year)
            if target_value is not None:
                constraint_values.append(target_value)
            else:
                constraint_values.append(0.0)

        # Create datasets
        datasets = []

        # Line item dataset
        line_item_dataset = ChartDataSet(
            label=line_item_label,
            data=line_item_values,
            color="blue",
            type=line_item_type,
        )
        datasets.append(line_item_dataset)

        # Constraint target dataset
        constraint_dataset = ChartDataSet(
            label=f"{constraint_results.label} Target",
            data=constraint_values,
            color="red",
            type=constraint_type,
        )
        datasets.append(constraint_dataset)

        # Create chart configuration
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=f"{line_item_label} vs {constraint_results.label} Target",
            value_format=value_format,
        )

        # Render the chart with Plotly
        fig = chart.to_plotly(width=width, height=height, template=template)

        return fig
