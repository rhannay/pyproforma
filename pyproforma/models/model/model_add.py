from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Model 

from ..line_item import LineItem, Category
from pyproforma.generators.generator_class import Generator

class AddNamespace:
    def __init__(self, model: 'Model'):
        """Initialize a new namespace for the given Model instance."""
        self._model = model

    def generator(self, generator: Generator):
        """
        Add a new generator to the model.
        
        This method accepts a Generator instance (must be a subclass of Generator).
        It validates the addition by first testing it on a copy of the model,
        then applies the change to the actual model if successful.
        
        Note: Generators are complex objects that are always passed as instances
        since they are subclasses with varying constructor arguments.
        
        Usage:
            # Create and add a generator instance
            debt_generator = Debt(name="loan", par_amounts={2023: 100000}, 
                                interest_rate=0.05, term=5)
            model.add.generator(debt_generator)
        
        Args:
            generator (Generator): A Generator instance to add to the model
            
        Returns:
            None
            
        Raises:
            ValueError: If the generator cannot be added (validation fails)
            TypeError: If the provided object is not a Generator instance
        """
        # Validate that a Generator instance is provided
        if not isinstance(generator, Generator):
            raise TypeError("Must provide a Generator instance")
        
        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy.generators.append(generator)
            model_copy._reclalculate()
            
            # If we get here, the addition was successful on the copy
            # Now apply it to the actual model
            self._model.generators.append(generator)
            self._model._reclalculate()
            
        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to add generator '{generator.name}': {str(e)}") from e

    def category(
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
            model.add.category(existing_category)
            
            # Method 2: Create from parameters
            model.add.category(name="assets", label="Assets", include_total=True)
        
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

    def line_item(
        self,
        line_item: LineItem = None,
        *,
        name: str = None,
        category: str = None,
        label: str = None,
        values: dict[int, float] = None,
        formula: str = None,
        value_format: str = 'no_decimals'
    ):
        """
        Add a new line item to the model.
        
        This method accepts either an already-created LineItem instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of 
        the model, then applies the change to the actual model if successful.
        
        Usage:
            # Method 1: Pass a LineItem instance
            model.add.line_item(existing_line_item)
            
            # Method 2: Create from parameters
            model.add.line_item(name="revenue", category="income", values={2023: 100000})
        
        Args:
            line_item (LineItem, optional): An already-created LineItem instance to add
            name (str, optional): Name for new LineItem - required if line_item is None
            category (str, optional): Category for new LineItem - required if line_item is None
            label (str, optional): Human-readable display name. Defaults to name if not provided.
            values (dict[int, float], optional): Dictionary mapping years to explicit values
            formula (str, optional): Formula string for calculating values
            value_format (str, optional): Format for displaying values. Defaults to 'no_decimals'
            
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
