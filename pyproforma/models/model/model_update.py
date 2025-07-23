from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Model 

from ..line_item import LineItem, Category
from ...constants import ValueFormat


class UpdateNamespace:
    def __init__(self, model: 'Model'):
        """Initialize an update namespace for the given Model instance."""
        self._model = model

    # ============================================================================
    # ADD METHODS (formerly AddNamespace methods)
    # ============================================================================



    def add_category(
        self,
        category: Category = None,
        *,
        name: str = None,
        label: str = None,
        total_label: str = None,
        include_total: bool = True
    ):
        """
        Add a new category to the model.
        
        This method accepts either an already-created Category instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Usage:
            # Method 1: Pass a Category instance
            model.update.add_category(existing_category)
            
            # Method 2: Create from parameters
            model.update.add_category(name="assets", label="Assets", include_total=True)
        
        Args:
            category (Category, optional): An already-created Category instance to add
            name (str, optional): Name for new Category - required if category is None
            label (str, optional): Human-readable display name. Defaults to name if not provided.
            total_label (str, optional): Label for the category total. Defaults to "Total {label}"
            include_total (bool, optional): Whether to include a total for this category. Defaults to True
            
        Returns:
            None
            
        Raises:
            ValueError: If the category cannot be added (validation fails), or if both
                category and name are provided, or if neither is provided
        """
        # Validate that exactly one of category or name is provided
        if category is not None and name is not None:
            raise ValueError("Cannot specify both 'category' and 'name' parameters. Use one or the other.")
        
        if category is None and name is None:
            raise ValueError("Must specify either 'category' parameter or 'name' parameter.")
        
        # Handle the case where a Category instance is passed
        if category is not None:
            new_category = category
        else:
            # Handle the case where parameters are passed to create a new Category
            try:
                new_category = Category(
                    name=name,
                    label=label,
                    total_label=total_label,
                    include_total=include_total
                )
            except ValueError as e:
                # Re-raise Category creation errors with our standard format
                raise ValueError(f"Failed to add category '{name}': {str(e)}") from e
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy._category_definitions.append(new_category)
            model_copy._reclalculate()
            
            # If we get here, the addition was successful on the copy
            # Now apply it to the actual model
            self._model._category_definitions.append(new_category)
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to add category '{new_category.name}': {str(e)}") from e

    def add_line_item(
        self,
        line_item: LineItem = None,
        *,
        name: str = None,
        category: str = None,
        label: str = None,
        values: dict[int, float] = None,
        formula: str = None,
        value_format: ValueFormat = 'no_decimals'
    ):
        """
        Add a new line item to the model.
        
        This method accepts either an already-created LineItem instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Usage:
            # Method 1: Pass a LineItem instance
            model.update.add_line_item(existing_line_item)
            
            # Method 2: Create from parameters
            model.update.add_line_item(name="revenue", category="income", values={2023: 100000})
        
        Args:
            line_item (LineItem, optional): An already-created LineItem instance to add
            name (str, optional): Name for new LineItem - required if line_item is None
            category (str, optional): Category for new LineItem - required if line_item is None
            label (str, optional): Human-readable display name. Defaults to name if not provided.
            values (dict[int, float], optional): Dictionary mapping years to explicit values
            formula (str, optional): Formula string for calculating values
            value_format (ValueFormat, optional): Format for displaying values. Defaults to 'no_decimals'
            
        Returns:
            None
            
        Raises:
            ValueError: If the line item cannot be added (validation fails), or if both
                line_item and name are provided, or if neither is provided
            TypeError: If name is provided but category is missing
        """
        # Validate that exactly one of line_item or name is provided
        if line_item is not None and name is not None:
            raise ValueError("Cannot specify both 'line_item' and 'name' parameters. Use one or the other.")
        
        if line_item is None and name is None:
            raise ValueError("Must specify either 'line_item' parameter or 'name' parameter.")
        
        # Handle the case where a LineItem instance is passed
        if line_item is not None:
            new_line_item = line_item
        else:
            # Handle the case where parameters are passed to create a new LineItem
            if category is None:
                raise TypeError("When creating a new LineItem, 'category' parameter is required")
            
            # Create the new line item - this will validate the name format
            try:
                new_line_item = LineItem(
                    name=name,
                    category=category,
                    label=label,
                    values=values,
                    formula=formula,
                    value_format=value_format
                )
            except ValueError as e:
                # Re-raise LineItem creation errors with our standard format
                raise ValueError(f"Failed to add line item '{name}': {str(e)}") from e
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy._line_item_definitions.append(new_line_item)
            model_copy._reclalculate()
            
            # If we get here, the addition was successful on the copy
            # Now apply it to the actual model
            self._model._line_item_definitions.append(new_line_item)
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to add line item '{new_line_item.name}': {str(e)}") from e

    # ============================================================================
    # UPDATE METHODS (formerly UpdateNamespace methods)
    # ============================================================================

    def update_category(
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
            model.update.update_category("income", label="Revenue Streams")
            
            # Rename a category (this updates line items automatically)
            model.update.update_category("old_name", new_name="new_name")
            
            # Replace with a Category instance
            model.update.update_category("income", category=new_category)
        
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

    def update_line_item(
        self,
        name: str,
        *,
        line_item: LineItem = None,
        new_name: str = None,
        category: str = None,
        label: str = None,
        values: dict[int, float] = None,
        formula: str = None,
        value_format: ValueFormat = None
    ):
        """
        Update a line item in the model by name.
        
        This method can update specific attributes of an existing line item or replace
        it entirely with a new LineItem instance. It validates the update by first 
        testing it on a copy of the model, then applies the change to the actual model 
        if successful.
        
        Usage:
            # Update specific attributes
            model.update.update_line_item("revenue", values={2023: 150000}, label="New Revenue")
            
            # Rename a line item
            model.update.update_line_item("old_name", new_name="new_name")
            
            # Replace with a LineItem instance
            model.update.update_line_item("revenue", line_item=new_line_item)
        
        Args:
            name (str): Name of the existing line item to update
            line_item (LineItem, optional): New LineItem instance to replace the existing one
            new_name (str, optional): New name for the line item
            category (str, optional): New category for the line item
            label (str, optional): New label for the line item
            values (dict[int, float], optional): New values dictionary for the line item
            formula (str, optional): New formula string for the line item
            value_format (ValueFormat, optional): New value format for the line item
            
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



    def update_years(self, new_years: list[int]):
        """
        Update the years in the model.
        
        This method updates the model's years attribute and recalculates the value matrix
        for the new year range. It validates the update by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Line items with values for years not in the new list will retain those values,
        but they won't be accessible through the model until those years are added back.
        
        Usage:
            # Update years to a new range
            model.update.update_years([2024, 2025, 2026])
            
            # Extend years
            model.update.update_years([2023, 2024, 2025, 2026, 2027])
        
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

    # ============================================================================
    # DELETE METHODS (formerly DeleteNamespace methods)
    # ============================================================================



    def delete_category(self, name: str):
        """
        Delete a category from the model by name.
        
        This method validates the deletion by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        Note that deleting a category will fail if there are line items that 
        reference this category.
        
        Usage:
            model.update.delete_category("old_category")
        
        Args:
            name (str): Name of the category to delete
            
        Returns:
            None
            
        Raises:
            ValueError: If the category cannot be deleted (validation fails), 
                       such as when line items still reference this category
            KeyError: If the category with the given name is not found
        """
        # Verify the category exists
        category_to_delete = None
        for category in self._model._category_definitions:
            if category.name == name:
                category_to_delete = category
                break
        
        if category_to_delete is None:
            raise KeyError(f"Category '{name}' not found in model")
        
        # Check if any line items reference this category
        line_items_using_category = [item for item in self._model._line_item_definitions if item.category == name]
        if line_items_using_category:
            item_names = [item.name for item in line_items_using_category]
            raise ValueError(f"Cannot delete category '{name}' because it is used by line items: {', '.join(item_names)}")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove the category from the copy
            model_copy._category_definitions = [category for category in model_copy._category_definitions if category.name != name]
            model_copy._reclalculate()
            
            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model._category_definitions = [category for category in self._model._category_definitions if category.name != name]
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete category '{name}': {str(e)}") from e

    def delete_line_item(self, name: str):
        """
        Delete a line item from the model by name.
        
        This method validates the deletion by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Usage:
            model.update.delete_line_item("expense_item")
        
        Args:
            name (str): Name of the line item to delete
            
        Returns:
            None
            
        Raises:
            ValueError: If the line item cannot be deleted (validation fails)
            KeyError: If the line item with the given name is not found
        """
        # Verify the line item exists
        try:
            line_item_to_delete = self._model.get_line_item_definition(name)
        except KeyError:
            raise KeyError(f"Line item '{name}' not found in model")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove the line item from the copy
            model_copy._line_item_definitions = [item for item in model_copy._line_item_definitions if item.name != name]
            model_copy._reclalculate()
            
            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model._line_item_definitions = [item for item in self._model._line_item_definitions if item.name != name]
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete line item '{name}': {str(e)}") from e