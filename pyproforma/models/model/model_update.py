from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Model 

from ..line_item import LineItem, Category
from pyproforma.generators.generator_class import Generator


class UpdateNamespace:
    def __init__(self, model: 'Model'):
        """Initialize an update namespace for the given Model instance."""
        self._model = model

    def category(
        self,
        name: str,
        *,
        category: Category = None,
        new_name: str = None,
        label: str = None,
        total_label: str = None,
        include_total: bool = None
    ):
        """
        Update a category in the model by name.
        
        This method can update specific attributes of an existing category or replace
        it entirely with a new Category instance. It validates the update by first 
        testing it on a copy of the model, then applies the change to the actual model 
        if successful.
        
        Note: Changing a category name will update all line items that reference it.
        
        Usage:
            # Update specific attributes
            model.update.category("income", label="Revenue Streams")
            
            # Rename a category (this updates line items automatically)
            model.update.category("old_name", new_name="new_name")
            
            # Replace with a Category instance
            model.update.category("income", category=new_category)
        
        Args:
            name (str): Name of the existing category to update
            category (Category, optional): New Category instance to replace the existing one
            new_name (str, optional): New name for the category
            label (str, optional): New label for the category
            total_label (str, optional): New total label for the category
            include_total (bool, optional): Whether to include a total for this category
            
        Returns:
            None
            
        Raises:
            ValueError: If the category cannot be updated (validation fails)
            KeyError: If the category with the given name is not found
        """
        # Find the existing category
        existing_category = None
        for category_item in self._model._category_definitions:
            if category_item.name == name:
                existing_category = category_item
                break
        
        if existing_category is None:
            raise KeyError(f"Category '{name}' not found in model")
        
        # If a Category instance is provided, use it as the replacement
        if category is not None:
            updated_category = category
        else:
            # Create an updated category based on the existing one
            try:
                updated_category = Category(
                    name=new_name if new_name is not None else existing_category.name,
                    label=label if label is not None else existing_category.label,
                    total_label=total_label if total_label is not None else existing_category.total_label,
                    include_total=include_total if include_total is not None else existing_category.include_total
                )
            except ValueError as e:
                # Re-raise Category creation errors with our standard format
                raise ValueError(f"Failed to update category '{name}': {str(e)}") from e
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            
            # Find and replace the category in the copy
            for i, category_item in enumerate(model_copy._category_definitions):
                if category_item.name == name:
                    model_copy._category_definitions[i] = updated_category
                    break
            
            # If the category name changed, update all line items that reference it
            if updated_category.name != name:
                for line_item in model_copy._line_item_definitions:
                    if line_item.category == name:
                        line_item.category = updated_category.name
            
            model_copy._reclalculate()
            
            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            for i, category_item in enumerate(self._model._category_definitions):
                if category_item.name == name:
                    self._model._category_definitions[i] = updated_category
                    break
            
            # Update line items if category name changed
            if updated_category.name != name:
                for line_item in self._model._line_item_definitions:
                    if line_item.category == name:
                        line_item.category = updated_category.name
            
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update category '{name}': {str(e)}") from e

    def line_item(
        self,
        name: str,
        *,
        line_item: LineItem = None,
        new_name: str = None,
        category: str = None,
        label: str = None,
        values: dict[int, float] = None,
        formula: str = None,
        value_format: str = None
    ):
        """
        Update a line item in the model by name.
        
        This method can update specific attributes of an existing line item or replace
        it entirely with a new LineItem instance. It validates the update by first 
        testing it on a copy of the model, then applies the change to the actual model 
        if successful.
        
        Usage:
            # Update specific attributes
            model.update.line_item("revenue", values={2023: 150000}, label="New Revenue")
            
            # Rename a line item
            model.update.line_item("old_name", new_name="new_name")
            
            # Replace with a LineItem instance
            model.update.line_item("revenue", line_item=new_line_item)
        
        Args:
            name (str): Name of the existing line item to update
            line_item (LineItem, optional): New LineItem instance to replace the existing one
            new_name (str, optional): New name for the line item
            category (str, optional): New category for the line item
            label (str, optional): New label for the line item
            values (dict[int, float], optional): New values dictionary for the line item
            formula (str, optional): New formula string for the line item
            value_format (str, optional): New value format for the line item
            
        Returns:
            None
            
        Raises:
            ValueError: If the line item cannot be updated (validation fails)
            KeyError: If the line item with the given name is not found
        """
        # Find the existing line item
        try:
            existing_item = self._model.get_line_item_definition(name)
        except KeyError:
            raise KeyError(f"Line item '{name}' not found in model")
        
        # If a LineItem instance is provided, use it as the replacement
        if line_item is not None:
            updated_item = line_item
        else:
            # Create an updated line item based on the existing one
            try:
                updated_item = LineItem(
                    name=new_name if new_name is not None else existing_item.name,
                    category=category if category is not None else existing_item.category,
                    label=label if label is not None else existing_item.label,
                    values=values if values is not None else existing_item.values,
                    formula=formula if formula is not None else existing_item.formula,
                    value_format=value_format if value_format is not None else existing_item.value_format
                )
            except ValueError as e:
                # Re-raise LineItem creation errors with our standard format
                raise ValueError(f"Failed to update line item '{name}': {str(e)}") from e
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Find and replace the line item in the copy
            for i, item in enumerate(model_copy._line_item_definitions):
                if item.name == name:
                    model_copy._line_item_definitions[i] = updated_item
                    break
            model_copy._reclalculate()
            
            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            for i, item in enumerate(self._model._line_item_definitions):
                if item.name == name:
                    self._model._line_item_definitions[i] = updated_item
                    break
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update line item '{name}': {str(e)}") from e

    def generator(
        self,
        name: str,
        *,
        generator: Generator
    ):
        """
        Update a generator in the model by name.
        
        This method replaces an existing generator entirely with a new Generator 
        instance. Unlike other update methods, this only supports full replacement
        and does not allow updating individual properties.
        
        It validates the update by first testing it on a copy of the model, 
        then applies the change to the actual model if successful.
        
        Usage:
            # Replace with a new Generator instance
            model.update.generator("debt_service", generator=new_debt_generator)
        
        Args:
            name (str): Name of the existing generator to update
            generator (Generator): New Generator instance to replace the existing one
            
        Returns:
            None
            
        Raises:
            ValueError: If the generator cannot be updated (validation fails)
            KeyError: If the generator with the given name is not found
            TypeError: If generator is not a Generator instance
        """
        # Validate that generator is a Generator instance
        if not isinstance(generator, Generator):
            raise TypeError(f"Expected Generator instance, got {type(generator).__name__}")
        
        # Find the existing generator
        existing_generator = None
        generator_index = None
        for i, gen in enumerate(self._model.generators):
            if gen.name == name:
                existing_generator = gen
                generator_index = i
                break
        
        if existing_generator is None:
            raise KeyError(f"Generator '{name}' not found in model")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Replace the generator in the copy
            model_copy.generators[generator_index] = generator
            model_copy._reclalculate()
            
            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            self._model.generators[generator_index] = generator
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update generator '{name}': {str(e)}") from e

    def years(self, new_years: list[int]):
        """
        Update the years in the model.
        
        This method updates the model's years attribute and recalculates the value matrix
        for the new year range. It validates the update by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Line items with values for years not in the new list will retain those values,
        but they won't be accessible through the model until those years are added back.
        
        Usage:
            # Update years to a new range
            model.update.years([2024, 2025, 2026])
            
            # Extend years
            model.update.years([2023, 2024, 2025, 2026, 2027])
        
        Args:
            new_years (list[int]): New list of years for the model
            
        Returns:
            None
            
        Raises:
            ValueError: If the years list is invalid (empty, non-integers, etc.)
            TypeError: If new_years is not a list
        """
        # Validate input
        if not isinstance(new_years, list):
            raise TypeError(f"Expected list, got {type(new_years).__name__}")
        
        if not new_years:
            raise ValueError("Years cannot be an empty list")
        
        if not all(isinstance(year, int) for year in new_years):
            raise ValueError("All years must be integers")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Update years and recalculate (remove duplicates and sort)
            model_copy.years = sorted(list(set(new_years)))
            model_copy._reclalculate()
            
            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            self._model.years = sorted(list(set(new_years)))
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update years: {str(e)}") from e
