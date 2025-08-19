from .table_class import Table, Cell, Row, Column
from .table_generator import generate_table_from_template
from typing import TYPE_CHECKING, Optional
from . import row_types as rt

if TYPE_CHECKING:
    from pyproforma import Model 


class Tables:
    """
    A namespace for table creation methods within a Pyproforma model.
    
    The Tables class provides a comprehensive interface for generating various types
    of tables from a Pyproforma Model. It serves as the primary entry point for
    creating formatted tables that display model data, including line items,
    categories, constraints, and custom templates.
    
    This class is typically accessed through a Model instance's `tables` attribute
    and provides methods to generate tables for different aspects of the financial
    model, such as individual line items, category summaries, constraint analysis,
    and comprehensive model overviews.
    
    Attributes:
        _model (Model): The underlying Pyproforma model containing the data
            and definitions used for table generation.
    
    Examples:
        >>> model = Model(...)  # Initialize with required parameters
        >>> table = model.tables.category('revenue')
        >>> all_items_table = model.tables.all()
    """
    
    def __init__(self, model: 'Model'):
        """Initialize the main tables namespace with a Model."""
        self._model = model
    
    def from_template(self, template: list[dict], include_name: bool=False) -> Table:
        """
        Generate a table from a template of row configurations.
        
        Args:
            template (list[dict]): A list of row configuration dictionaries that define
                the structure and content of the table. Each dictionary should specify
                the row type and its parameters (e.g., ItemRow, LabelRow, etc.).
            include_name (bool, optional): Whether to include a name column in the 
                generated table. Defaults to False.
        
        Returns:
            Table: A Table object containing the rows and data as specified by the template.
        
        Example:
            >>> template = [
            ...     rt.LabelRow(label='Revenue', bold=True),
            ...     rt.ItemRow(name='sales_revenue'),
            ...     rt.ItemRow(name='other_revenue')
            ... ]
            >>> table = tables.from_template(template, include_name=True)
        """
        table = generate_table_from_template(self._model, template, include_name=include_name)
        return table
    
    def all(self) -> Table:
        """
        Generate a comprehensive table containing all model items.
        
        Creates a complete overview table that includes all line items
        organized by category, and any line item generator items. The table is
        structured with clear section headers and includes a name column for
        easy identification of each item.
        
        Returns:
            Table: A Table object containing all model items organized by type:
                - LINE ITEMS: All line items organized by category
                - LINE ITEM GENERATOR ITEMS: All generated line items
        
        Examples:
            >>> table = model.tables.all()  # Returns a comprehensive table with all model components
        """
        rows = []
        # Line Items (including all categories)
        if self._model._category_definitions:
            rows.append(rt.LabelRow(label='LINE ITEMS', bold=True))
            for cat_def in self._model._category_definitions:
                rows.extend(self._category_rows(cat_def.name))
        # Line Item Generator items
        if self._model.line_item_generators:
            rows.append(rt.LabelRow(label='LINE ITEM GENERATOR ITEMS', bold=True))
            for generator in self._model.line_item_generators:
                for gen_name in generator.defined_names:
                    rows.append(rt.ItemRow(name=gen_name))
        return generate_table_from_template(self._model, rows, include_name=True)

    def line_items(self) -> Table:
        """
        Generate a table containing all line items organized by category.
        
        Creates a table that displays all line items from the model, organized
        by their respective categories. Each category is shown with a bold header
        followed by its line items, and includes category totals if configured.
        
        Returns:
            Table: A Table object containing all line items grouped by category.
        
        Examples:
            >>> table = model.tables.line_items()
        """
        rows = self._line_item_rows()
        return self.from_template(rows)
    
    def _line_item_rows(self):
        rows = []
        for cat_def in self._model._category_definitions:
            rows.extend(self._category_rows(cat_def.name))
        return rows
    
    def _category_rows(self, category_name: str):
        rows = []
        category = self._model.category(category_name)
        rows.append(rt.LabelRow(label=category.category_obj.label, bold=True))
        for item in category.line_items_definitions:
            rows.append(rt.ItemRow(name=item.name))
        if category.category_obj.include_total:
            rows.append(rt.ItemRow(name=category.category_obj.total_name, bold=True))
        return rows

    def category(self, category_name: str, include_name: bool = False) -> Table:
        """
        Generate a table for a specific category.
        
        Args:
            category_name (str): The name of the category to generate the table for.
            include_name (bool, optional): Whether to include the name column. Defaults to False.
        
        Returns:
            Table: A Table object containing the category items.
        """
        rows = self._category_rows(category_name)
        return self.from_template(rows, include_name=include_name)

    def line_item(self, name: str, include_name: bool = False, hardcoded_color: Optional[str] = None) -> Table:
        """
        Generate a table for a specific line item showing its label and values by year.
        
        Args:
            name (str): The name of the line item to generate the table for.
            include_name (bool, optional): Whether to include the name column. Defaults to False.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be 
                                           displayed in this color. Defaults to None.
        
        Returns:
            Table: A Table object containing the line item's label and values across years.
        """
        rows = [
            rt.ItemRow(name=name, hardcoded_color=hardcoded_color),
            rt.PercentChangeRow(name=name, label='% Change'),
            rt.CumulativeChangeRow(name=name, label='Cumulative Change'),
            rt.CumulativePercentChangeRow(name=name, label='Cumulative % Change')
        ]
        return self.from_template(rows, include_name=include_name)

    def constraint(self, constraint_name: str, color_code: bool = True) -> Table:
        """
        Generate a table for a specific constraint showing its line item, target, variance, and pass/fail status.
        
        Args:
            constraint_name (str): The name of the constraint to generate the table for.
            color_code (bool, optional): Whether to apply color coding to the table. Defaults to True.
        
        Returns:
            Table: A Table object containing the constraint's line item, target, variance, and pass/fail rows.
        """
        constraint = self._model.get_constraint_definition(constraint_name)
        rows = [
            rt.LabelRow(label=constraint.label, bold=True),
            rt.ItemRow(name=constraint.line_item_name),
            rt.ConstraintTargetRow(constraint_name=constraint_name, label='Target'),
            rt.ConstraintVarianceRow(constraint_name=constraint_name, label='Variance'),
            rt.ConstraintPassRow(constraint_name=constraint_name, label='Pass/Fail', color_code=color_code)
        ]
        return generate_table_from_template(self._model, rows, include_name=False)


