from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma import Model 


class DeleteNamespace:
    def __init__(self, model: 'Model'):
        """Initialize a delete namespace for the given Model instance."""
        self._model = model

    def generator(self, name: str):
        """
        Delete a generator from the model by name.
        
        This method validates the deletion by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        Note that deleting a generator will fail if there are formulas that 
        reference any of the variables this generator provides.
        
        Usage:
            model.delete.generator("debt_generator")
        
        Args:
            name (str): Name of the generator to delete
            
        Returns:
            None
            
        Raises:
            ValueError: If the generator cannot be deleted (validation fails),
                       such as when formulas reference variables from this generator
            KeyError: If the generator with the given name is not found
        """
        # Verify the generator exists
        generator_to_delete = None
        for generator in self._model.generators:
            if generator.name == name:
                generator_to_delete = generator
                break
        
        if generator_to_delete is None:
            raise KeyError(f"Generator '{name}' not found in model")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove the generator from the copy
            model_copy.generators = [generator for generator in model_copy.generators if generator.name != name]
            model_copy._reclalculate()
            
            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model.generators = [generator for generator in self._model.generators if generator.name != name]
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete generator '{name}': {str(e)}") from e

    def category(self, name: str):
        """
        Delete a category from the model by name.
        
        This method validates the deletion by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        Note that deleting a category will fail if there are line items that 
        reference this category.
        
        Usage:
            model.delete.category("old_category")
        
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

    def line_item(self, name: str):
        """
        Delete a line item from the model by name.
        
        This method validates the deletion by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Usage:
            model.delete.line_item("expense_item")
        
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
