from .table_class import Table, Cell, Row, Column
from .table_generator import generate_table
from typing import TYPE_CHECKING
from . import row_types as rt

if TYPE_CHECKING:
    from pyproforma import Model 


class Tables:
    def __init__(self, model: 'Model'):
        """Initialize the main tables namespace with a Model."""
        self._model = model
    
    def generate_table(self, template: list[dict], include_name: bool=False) -> Table:
        """Generate a table for the specified items."""
        table = generate_table(self._model, template, include_name=include_name)
        return table
    
    def all(self):
        rows = []
        # Assumptions (now as line items with category 'assumptions')
        assumption_items = [item for item in self._model._line_item_definitions if item.category == 'assumptions']
        if assumption_items:
            rows.append(rt.LabelRow(label='ASSUMPTIONS', bold=True))
            for a_def in assumption_items:
                rows.append(rt.ItemRow(name=a_def.name))
        # Line Items (excluding assumptions to avoid duplication)
        non_assumption_categories = [cat for cat in self._model._category_definitions if cat.name != 'assumptions']
        if non_assumption_categories:
            rows.append(rt.LabelRow(label='LINE ITEMS', bold=True))
            for cat_def in non_assumption_categories:
                rows.extend(self._category_rows(cat_def.name))
        # Line Item Generator items
        if self._model.line_item_generators:
            rows.append(rt.LabelRow(label='LINE ITEM GENERATOR ITEMS', bold=True))
            for generator in self._model.line_item_generators:
                for gen_name in generator.defined_names:
                    rows.append(rt.ItemRow(name=gen_name))
        return generate_table(self._model, rows, include_name=True)
       
    def line_items(self):
        rows = self._line_item_rows()
        return self.generate_table(rows)
    
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
    
    def category(self, category_name: str):
        """
        Generate a table for a specific category.
        
        Args:
            category_name (str): The name of the category to generate the table for.
        
        Returns:
            Table: A Table object containing the category items.
        """
        rows = self._category_rows(category_name)
        return self.generate_table(rows, include_name=True)
    
    def line_item(self, name: str):
        """
        Generate a table for a specific line item showing its label and values by year.
        
        Args:
            name (str): The name of the line item to generate the table for.
        
        Returns:
            Table: A Table object containing the line item's label and values across years.
        """
        rows = [
            rt.ItemRow(name=name),
            rt.PercentChangeRow(name=name, label='% Change'),
            rt.CumulativeChangeRow(name=name, label='Cumulative Change'),
            rt.CumulativePercentChangeRow(name=name, label='Cumulative % Change')
        ]
        return self.generate_table(rows, include_name=True)
    
    def constraint(self, constraint_name: str, color_code: bool = True):
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
        return generate_table(self._model, rows, include_name=False)


