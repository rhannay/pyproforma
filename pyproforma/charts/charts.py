from typing import TYPE_CHECKING, Union
from .chart_class import Chart, ChartDataSet
from ..constants import ValueFormat

if TYPE_CHECKING:
    from pyproforma import Model 


class Charts:
    def __init__(self, model: 'Model'):
        """Initialize the main charts namespace with a Model."""
        self._model = model
    
    def item(self, name: str, width: int = 800, height: int = 600, template: str = 'plotly_white', chart_type: str = 'line'):
        """
        Create a chart using Plotly showing the values for a given name over years.
        
        Args:
            name (str): The name of the item to chart (line item, assumption, etc.)
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')
            
        Returns:
            Chart figure: The Plotly chart figure
            
        Raises:
            KeyError: If the name is not found in the model
        """
        # Get the item info and label for display
        try:
            label = self._model.li(name).label
            value_format = self._model.li(name).value_format
        except KeyError:
            raise KeyError(f"Name '{name}' not found in model defined names.")
        
        # Get values for all years
        years = self._model.years
        values = []
        for year in years:
            try:
                value = self._model.get_value(name, year)
                values.append(value)
            except KeyError:
                values.append(0.0)
        
        # Create dataset
        dataset = ChartDataSet(
            label=label,
            data=values,
            color='blue',
            type=chart_type
        )
        
        # Create chart configuration
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=[dataset],
            title=f"{label} Over Time",
            value_format=value_format
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig
    
    def items(self, item_names: list[str], width: int = 800, height: int = 600, template: str = 'plotly_white', value_format: ValueFormat = None):
        """
        Create a line chart using Plotly showing the values for multiple items over years.
        
        Args:
            item_names (list[str]): List of item names to chart (line items, assumptions, etc.)
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            value_format (ValueFormat, optional): Y-axis value format. If None, uses the first item's format.
            
        Returns:
            Chart figure: The Plotly chart figure with multiple lines
            
        Raises:
            KeyError: If any name is not found in the model
        """
        if not item_names:
            raise ValueError("item_names list cannot be empty")
        
        # Get years once for all items
        years = self._model.years
        datasets = []
        
        # Get value_format from the parameter or first item
        if value_format is None:
            try:
                value_format = self._model.li(item_names[0]).value_format
            except KeyError:
                raise KeyError(f"Name '{item_names[0]}' not found in model defined names.")
        
        # # Define colors for multiple lines (cycles through if more items than colors)
        # colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.li(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")
            
            # Get values for all years
            values = []
            for year in years:
                try:
                    value = self._model.get_value(name, year)
                    values.append(value)
                except KeyError:
                    values.append(0.0)
            
            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=label,
                data=values,
                # color=colors[i % len(colors)],
                type='line'
            )
            datasets.append(dataset)
        
        # Create chart configuration
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title="Multiple Items Over Time",
            value_format=value_format
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig
    
    def cumulative_percent_change(self, item_names: Union[str, list[str]], width: int = 800, height: int = 600, template: str = 'plotly_white', start_year: int = None):
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
            KeyError: If any name is not found in the model
            ValueError: If any name refers to an assumption (not supported for cumulative percent change)
        """
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]
        
        if not item_names:
            raise ValueError("item_names cannot be empty")
        
        # Get years once for all items
        years = self._model.years
        datasets = []
        
        # Define colors for multiple lines (cycles through if more items than colors)
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.li(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")
            
            # Get cumulative percent change values for all years
            values = []
            for year in years:
                try:
                    cum_pct_change = self._model.cumulative_percent_change(name, year, start_year=start_year)
                    # Convert to percentage (multiply by 100) for better chart readability
                    if cum_pct_change is not None:
                        values.append(cum_pct_change)
                    else:
                        values.append(0.0)  # First year or when calculation not possible
                except (KeyError, ValueError) as e:
                    # Re-raise the error with context
                    raise e
            
            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=f"{label} Cumulative % Change",
                data=values,
                color=colors[i % len(colors)],
                type='line'
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
            value_format='percent'
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig
    
    def cumulative_change(self, item_names: Union[str, list[str]], width: int = 800, height: int = 600, template: str = 'plotly_white', start_year: int = None):
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
            KeyError: If any name is not found in the model
            ValueError: If any name refers to an assumption (not supported for cumulative change)
        """
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]
        
        if not item_names:
            raise ValueError("item_names cannot be empty")
        
        # Get years once for all items
        years = self._model.years
        datasets = []
        
        # Define colors for multiple lines (cycles through if more items than colors)
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.li(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")
            
            # Get cumulative change values for all years
            values = []
            for year in years:
                try:
                    cum_change = self._model.cumulative_change(name, year, start_year=start_year)
                    # Handle None values (like first year or when calculation not possible)
                    if cum_change is not None:
                        values.append(cum_change)
                    else:
                        values.append(0.0)  # First year or when calculation not possible
                except (KeyError, ValueError) as e:
                    # Re-raise the error with context
                    raise e
            
            # Create dataset with cycling colors
            dataset = ChartDataSet(
                label=f"{label} Cumulative Change",
                data=values,
                color=colors[i % len(colors)],
                type='line'
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
            value_format='currency'
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig
    
    def index_to_year(self, item_names: Union[str, list[str]], width: int = 800, height: int = 600, template: str = 'plotly_white', start_year: int = None):
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
            KeyError: If any name is not found in the model
            ValueError: If any name refers to an assumption (not supported for index_to_year)
        """
        # Convert single item to list for uniform processing
        if isinstance(item_names, str):
            item_names = [item_names]
        
        if not item_names:
            raise ValueError("item_names cannot be empty")
        
        # Get years once for all items
        years = self._model.years
        datasets = []
        
        # Define colors for multiple lines (cycles through if more items than colors)
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, name in enumerate(item_names):
            # Get the item info and label for display
            try:
                label = self._model.li(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")
            
            # Get indexed values for all years
            values = []
            for year in years:
                try:
                    indexed_value = self._model.index_to_year(name, year, start_year=start_year)
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
                type='line'
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
            value_format='number'
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig
    
    def line_items_pie(self, item_names: list[str], year: int, width: int = 800, height: int = 600, template: str = 'plotly_white'):
        """
        Create a pie chart using Plotly showing the values for multiple line items at a specific year.
        
        Args:
            item_names (list[str]): List of line item names to include in the pie chart
            year (int): The year for which to create the pie chart
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            
        Returns:
            Chart figure: The Plotly pie chart figure
            
        Raises:
            KeyError: If any name is not found in the model
            ValueError: If item_names list is empty or if year is not in model years
        """
        if not item_names:
            raise ValueError("item_names list cannot be empty")
        
        # Validate year is in model years
        years = self._model.years
        if year not in years:
            raise ValueError(f"Year {year} not found in model years: {years}")
        
        # Get values and labels for the specified year
        values = []
        labels = []
        
        # Get value_format from the first item (assuming all items have similar format)
        try:
            value_format = self._model.li(item_names[0]).value_format
        except KeyError:
            raise KeyError(f"Name '{item_names[0]}' not found in model defined names.")
        
        for name in item_names:
            # Get the item info and label for display
            try:
                label = self._model.li(name).label
            except KeyError:
                raise KeyError(f"Name '{name}' not found in model defined names.")
            
            # Get value for the specified year
            try:
                value = self._model.get_value(name, year)
                # Only include positive values in pie chart
                if value > 0:
                    values.append(value)
                    labels.append(label)
            except KeyError:
                # Skip items that don't have values for this year
                continue
        
        if not values:
            raise ValueError(f"No positive values found for the specified items in year {year}")
        
        # Create pie chart dataset
        dataset = ChartDataSet(
            label=f"Line Items Distribution ({year})",
            data=values,
            type='pie'
        )
        
        # Create chart configuration
        chart = Chart(
            labels=labels,
            data_sets=[dataset],
            title=f"Line Items Distribution - {year}",
            value_format=value_format
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template,
            show_legend=False
        )
                
        return fig
    
    def constraint(self, constraint_name: str, width: int = 800, height: int = 600, template: str = 'plotly_white', line_item_type: str = 'bar', constraint_type: str = 'line'):
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
            KeyError: If the constraint name is not found in the model
        """
        # Get the constraint
        try:
            constraint = self._model.get_constraint_definition(constraint_name)
        except KeyError:
            raise KeyError(f"Constraint '{constraint_name}' not found in model constraints.")
        
        # Get the associated line item info
        line_item_name = constraint.line_item_name
        try:
            line_item = self._model.li(line_item_name)
            line_item_label = line_item.label
            value_format = line_item.value_format
        except KeyError:
            raise KeyError(f"Line item '{line_item_name}' not found in model defined names.")
        
        # Get years
        years = self._model.years
        
        # Get line item values for all years
        line_item_values = []
        for year in years:
            try:
                value = self._model.get_value(line_item_name, year)
                line_item_values.append(value)
            except KeyError:
                line_item_values.append(0.0)
        
        # Get constraint target values for all years
        constraint_values = []
        for year in years:
            target_value = constraint.get_target(year)
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
            color='blue',
            type=line_item_type
        )
        datasets.append(line_item_dataset)
        
        # Constraint target dataset
        constraint_dataset = ChartDataSet(
            label=f"{constraint.label} Target",
            data=constraint_values,
            color='red',
            type=constraint_type
        )
        datasets.append(constraint_dataset)
        
        # Create chart configuration
        chart = Chart(
            labels=[str(year) for year in years],
            data_sets=datasets,
            title=f"{line_item_label} vs {constraint.label} Target",
            value_format=value_format
        )
        
        # Render the chart with Plotly
        fig = chart.to_plotly(
            width=width, 
            height=height, 
            template=template
        )
                
        return fig

