from typing import TYPE_CHECKING
import pandas as pd
from pyproforma.tables.table_class import format_value

if TYPE_CHECKING:
    from .model import Model
    from .line_item import LineItem, Category
    from .constraint import Constraint


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
        >>> revenue_item = model.item('revenue')
        >>> print(revenue_item)  # Shows summary info
        >>> revenue_item.values()  # Returns dict of year: value
        >>> revenue_item.to_series()  # Returns pandas Series
    """
    
    def __init__(self, model: 'Model', item_name: str):
        self.model = model 
        self.item_name = item_name
        self._line_item_metadata = model._get_item_metadata(item_name)
        self.source_type = self._line_item_metadata['source_type']
        self.label = self._line_item_metadata['label']
        self.value_format = self._line_item_metadata['value_format']
    
    def __str__(self) -> str:
        """Return a string representation showing key information about the item."""
        return self.summary()
    
    def __repr__(self) -> str:
        return f"LineItemResults(item_name='{self.item_name}', source_type='{self._line_item_metadata['source_type']}')"
    
    def values(self) -> dict[int, float]:
        """
        Return a dictionary of year: value for this item.
        
        Returns:
            dict[int, float]: Dictionary mapping years to item values
        """
        values = {}
        for year in self.model.years:
            values[year] = self.model.get_value(self.item_name, year)
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
        return self.model.get_value(self.item_name, year)
    
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
    
    def table(self):
        """
        Return a Table object for this item using the tables.item() function.
        
        Returns:
            Table: A Table object containing the item formatted for display
        """
        return self.model.tables.line_item(self.item_name)

    def chart(self, width: int = 800, height: int = 600, template: str = 'plotly_white', chart_type: str = 'line'):
        """
        Create a chart using Plotly showing the values for this item over years.
        
        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')
            
        Returns:
            Chart figure: The Plotly chart figure
            
        Raises:
            KeyError: If the item name is not found in the model
        """
        return self.model.charts.item(self.item_name, width=width, height=height, template=template, chart_type=chart_type)
    
    def cumulative_percent_change_chart(self, width: int = 800, height: int = 600, template: str = 'plotly_white'):
        """
        Create a chart showing cumulative percentage change from a base year.
        
        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            
        Returns:
            Chart figure: The Plotly chart figure showing cumulative change percentages
        """
        return self.model.charts.cumulative_percent_change(self.item_name, width=width, height=height, template=template)
    
    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        summary_text = self.summary()
        html_summary = summary_text.replace('\n', '<br>')
        return f'<pre>{html_summary}</pre>'
    
    def summary(self) -> str:
        """
        Return a summary string with key information about the item.
        
        Returns:
            str: Formatted summary of the item
        """
        # Get value for first year if available
        value_info = ""
        if self.model.years:
            first_year = self.model.years[0]
            try:
                value = self.model.get_value(self.item_name, first_year)
                formatted_value = format_value(value, self.value_format)
                value_info = f"\nValue ({first_year}): {formatted_value}"
            except KeyError:
                value_info = "\nValue: Not available"
        
        # Get formula information based on source type
        formula_info = ""
        if self.source_type == "line_item":
            try:
                line_item = self.model.get_line_item_definition(self.item_name)
                if line_item.formula:
                    formula_info = f"\nFormula: {line_item.formula}"
                else:
                    formula_info = "\nFormula: None (explicit values)"
            except KeyError:
                formula_info = "\nFormula: Not available"
        elif self.source_type == "category":
            formula_info = f"\nFormula: Sum of items in category '{self.item_name}'"
        
        return (f"LineItemResults('{self.item_name}')\n"
                f"Label: {self.label}\n"
                f"Source Type: {self.source_type}\n"
                f"Value Format: {self.value_format}{formula_info}{value_info}")


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
    
    def __init__(self, model: 'Model', category_name: str):
        self.model = model
        self.category_name = category_name
        self.category_obj = model.get_category_definition(category_name)
        self.line_items_definitions = model.get_line_item_definitions_by_category(category_name)
        self.line_item_names = model.get_line_item_names_by_category(category_name)
    
    def __str__(self) -> str:
        """
        Return a string representation showing key information about the category.
        """
        return self.summary()
    
    def __repr__(self) -> str:
        return f"CategoryResults(category_name='{self.category_name}', num_items={len(self.line_items_definitions)})"
        
    def totals(self) -> dict[int, float]:
        """
        Return a dictionary of year: total value for this category.
        
        Returns:
            dict[int, float]: Dictionary mapping years to category totals
            
        Raises:
            ValueError: If the category doesn't include totals
        """
        if not self.category_obj.include_total:
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
        """
        values = {}
        for item in self.line_items_definitions:
            values[item.name] = {}
            for year in self.model.years:
                try:
                    values[item.name][year] = self.model.get_value(item.name, year)
                except KeyError:
                    values[item.name][year] = 0.0
        
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
            df_data[year] = [values_dict[item.name][year] for item in self.line_items_definitions]
        
        df = pd.DataFrame(df_data, index=[item.name for item in self.line_items_definitions])
        
        # Add total row if category includes totals
        if self.category_obj.include_total:
            try:
                total_row = self.totals()
                df.loc[self.category_obj.total_name] = [total_row[year] for year in self.model.years]
            except (ValueError, KeyError):
                pass
        
        return df
    
    def table(self):
        """
        Return a Table object for this category using the tables.category() function.
        
        Returns:
            Table: A Table object containing the category items formatted for display
        """
        return self.model.tables.category(self.category_name)

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        summary_text = self.summary()
        # Convert newlines to HTML line breaks for proper notebook display
        html_summary = summary_text.replace('\n', '<br>')
        return f'<pre>{html_summary}</pre>'

    def summary(self) -> str:
        """
        Return a summary string with key statistics about the category.
        
        Returns:
            str: Formatted summary of the category
        """
        num_items = len(self.line_items_definitions)
        item_names = [item.name for item in self.line_items_definitions]
        
        # Get total for first year if category includes total
        total_info = ""
        if self.category_obj.include_total and self.model.years:
            first_year = self.model.years[0]
            try:
                total_value = self.model.category_total(self.category_name, first_year)
                total_info = f"\nTotal ({first_year}): {total_value:,.0f}"
            except (KeyError, AttributeError):
                total_info = "\nTotal: Not available"
        
        return (f"CategoryResults('{self.category_name}')\n"
                f"Label: {self.category_obj.label}\n"
                f"Line Items: {num_items}\n"
                f"Items: {', '.join(item_names)}{total_info}")


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
    """
    
    def __init__(self, model: 'Model', constraint_name: str):
        self.model = model
        self.constraint_name = constraint_name
        self.constraint_definition = model.get_constraint_definition(constraint_name)
        self.line_item_name = self.constraint_definition.line_item_name
    
    def __str__(self) -> str:
        """Return a string representation showing key information about the constraint."""
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
        return self.model.get_value(self.line_item_name, year)
    
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
        """
        return self.model.tables.constraint(self.constraint_name)

    def chart(self, width: int = 800, height: int = 600, template: str = 'plotly_white', line_item_type: str = 'bar', constraint_type: str = 'line'):
        """
        Create a chart using Plotly showing the values for this constraint over years.
        
        Args:
            width (int): Chart width in pixels (default: 800)
            height (int): Chart height in pixels (default: 600)
            template (str): Plotly template to use (default: 'plotly_white')
            chart_type (str): Type of chart to create - 'line', 'bar', etc. (default: 'line')
            
        Returns:
            Chart figure: The Plotly chart figure
            
        Raises:
            KeyError: If the constraint name is not found in the model
        """
        return self.model.charts.constraint(self.constraint_name, width=width, height=height, template=template, line_item_type=line_item_type, constraint_type=constraint_type)

    def evaluate(self, year: int) -> bool:
        """
        Evaluate whether the constraint is satisfied for a specific year.
        
        Args:
            year (int): The year to evaluate the constraint for
            
        Returns:
            bool: True if the constraint is satisfied, False otherwise
            
        Raises:
            ValueError: If year or line item is not found in the model, or no target available
        """
        return self.constraint_definition.evaluate(self.model._value_matrix, year)

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        summary_text = self.summary()
        html_summary = summary_text.replace('\n', '<br>')
        return f'<pre>{html_summary}</pre>'
    
    def summary(self) -> str:
        """
        Return a summary string with key information about the constraint.
        
        Returns:
            str: Formatted summary of the constraint
        """
        # Get value for first year if available
        value_info = ""
        if self.model.years:
            first_year = self.model.years[0]
            try:
                value = self.model.get_value(self.line_item_name, first_year)
                value_info = f"\nValue ({first_year}): {value:,.2f}"
            except KeyError:
                value_info = "\nValue: Not available"
        
        # Get constraint formula/expression
        formula_info = ""
        if hasattr(self.constraint_definition, 'expression') and self.constraint_definition.expression:
            formula_info = f"\nExpression: {self.constraint_definition.expression}"
        
        return (f"ConstraintResults('{self.constraint_name}')\n"
                f"Label: {getattr(self.constraint_definition, 'label', self.constraint_name)}\n"
                f"Type: {getattr(self.constraint_definition, 'constraint_type', 'Unknown')}{formula_info}{value_info}")
