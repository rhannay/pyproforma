from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Model

from ...constants import ValueFormat
from ..category import Category
from ..constraint import Constraint
from ..line_item import LineItem


class UpdateNamespace:
    def __init__(self, model: "Model") -> None:
        """Initialize an update namespace for the given Model instance."""
        self._model = model

    # ============================================================================
    # ADD METHODS (formerly AddNamespace methods)
    # ============================================================================

    def add_category(
        self,
        category: Category | None = None,
        *,
        name: str | None = None,
        label: str | None = None,
    ) -> None:
        """
        Add a new category to the model.

        This method accepts either an already-created Category instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Args:
            category (Category, optional): An already-created Category instance to add
            name (str, optional): Name for new Category - required if category is None
            label (str, optional): Human-readable display name. Defaults to name if not provided.

        Returns:
            None

        Raises:
            ValueError: If the category cannot be added (validation fails), or if both
                category and name are provided, or if neither is provided

        Examples:
            >>> # Method 1: Pass a Category instance
            >>> model.update.add_category(existing_category)

            >>> # Method 2: Create from parameters
            >>> model.update.add_category(name="assets", label="Assets")
        """  # noqa: E501
        # Validate that exactly one of category or name is provided
        if category is not None and name is not None:
            raise ValueError(
                "Cannot specify both 'category' and 'name' parameters. Use one or the other."  # noqa: E501
            )

        if category is None and name is None:
            raise ValueError(
                "Must specify either 'category' parameter or 'name' parameter."
            )

        # Handle the case where a Category instance is passed
        if category is not None:
            new_category = category
        else:
            # Handle the case where parameters are passed to create a new Category
            try:
                new_category = Category(
                    name=name,
                    label=label,
                )
            except ValueError as e:
                # Re-raise Category creation errors with our standard format
                raise ValueError(f"Failed to add category '{name}': {str(e)}") from e

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy._category_definitions.append(new_category)
            model_copy._build_and_calculate()

            # If we get here, the addition was successful on the copy
            # Now apply it to the actual model
            self._model._category_definitions.append(new_category)
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(
                f"Failed to add category '{new_category.name}': {str(e)}"
            ) from e

    def add_line_item(
        self,
        line_item: LineItem | None = None,
        *,
        name: str | None = None,
        category: str | None = None,
        label: str | None = None,
        values: dict[int, float] | None = None,
        formula: str | None = None,
        value_format: ValueFormat = "no_decimals",
        replace: bool = False,
    ) -> None:
        """
        Add a new line item to the model.

        This method accepts either an already-created LineItem instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Args:
            line_item (LineItem, optional): An already-created LineItem instance to add
            name (str, optional): Name for new LineItem - required if line_item is None
            category (str, optional): Category for new LineItem. Defaults to "general" if None
            label (str, optional): Human-readable display name. Defaults to name if not provided.
            values (dict[int, float], optional): Dictionary mapping years to explicit values
            formula (str, optional): Formula string for calculating values
            value_format (ValueFormat, optional): Format for displaying values. Defaults to 'no_decimals'
            replace (bool, optional): If True, replace existing line item with same name. Defaults to False.

        Returns:
            None

        Raises:
            ValueError: If the line item cannot be added (validation fails), or if both
                line_item and name are provided, or if neither is provided, or if a line item
                with the same name already exists and replace=False

        Examples:
            >>> # Method 1: Pass a LineItem instance
            >>> model.update.add_line_item(existing_line_item)

            >>> # Method 2: Create from parameters
            >>> model.update.add_line_item(name="revenue", category="income", values={2023: 100000})

            >>> # Method 3: Replace existing line item
            >>> model.update.add_line_item(name="revenue", values={2023: 150000}, replace=True)
        """  # noqa: E501
        # Validate that exactly one of line_item or name is provided
        if line_item is not None and name is not None:
            raise ValueError(
                "Cannot specify both 'line_item' and 'name' parameters. Use one or the other."  # noqa: E501
            )

        if line_item is None and name is None:
            raise ValueError(
                "Must specify either 'line_item' parameter or 'name' parameter."
            )

        # Handle the case where a LineItem instance is passed
        if line_item is not None:
            new_line_item = line_item
        else:
            # Handle the case where parameters are passed to create a new LineItem
            # Create the new line item - this will validate the name format
            try:
                new_line_item = LineItem(
                    name=name,
                    category=category,
                    label=label,
                    values=values,
                    formula=formula,
                    value_format=value_format,
                )
            except ValueError as e:
                # Re-raise LineItem creation errors with our standard format
                raise ValueError(f"Failed to add line item '{name}': {str(e)}") from e

        # Check if line item name already exists
        existing_names = [item.name for item in self._model._line_item_definitions]
        if new_line_item.name in existing_names and not replace:
            raise ValueError(
                f"Line item with name '{new_line_item.name}' already exists. "
                f"Use update.update_line_item() to modify existing line items, "
                f"or set replace=True to replace the existing item."
            )

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()

            if replace and new_line_item.name in existing_names:
                # Replace existing line item
                for i, item in enumerate(model_copy._line_item_definitions):
                    if item.name == new_line_item.name:
                        model_copy._line_item_definitions[i] = new_line_item
                        break
            else:
                # Add new line item
                model_copy._line_item_definitions.append(new_line_item)

            model_copy._build_and_calculate()

            # If we get here, the operation was successful on the copy
            # Now apply it to the actual model
            if replace and new_line_item.name in existing_names:
                # Replace existing line item
                for i, item in enumerate(self._model._line_item_definitions):
                    if item.name == new_line_item.name:
                        self._model._line_item_definitions[i] = new_line_item
                        break
            else:
                # Add new line item
                self._model._line_item_definitions.append(new_line_item)

            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            action = (
                "replace" if replace and new_line_item.name in existing_names else "add"
            )
            raise ValueError(
                f"Failed to {action} line item '{new_line_item.name}': {str(e)}"
            ) from e

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
    ) -> None:
        """
        Update a category in the model by name.

        This method can update specific attributes of an existing category or replace
        it entirely with a new Category instance. It validates the update by first
        testing it on a copy of the model, then applies the change to the actual model
        if successful.

        Note: Changing a category name will update all line items that reference it.

        Args:
            name (str): Name of the existing category to update
            category (Category, optional): New Category instance to replace the existing one
            new_name (str, optional): New name for the category
            label (str, optional): New label for the category

        Returns:
            None

        Raises:
            ValueError: If the category cannot be updated (validation fails)
            KeyError: If the category with the given name is not found

        Examples:
            >>> # Update specific attributes
            >>> model.update.update_category("income", label="Revenue Streams")

            >>> # Rename a category (this updates line items automatically)
            >>> model.update.update_category("old_name", new_name="new_name")

            >>> # Replace with a Category instance
            >>> model.update.update_category("income", category=new_category)
        """  # noqa: E501
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

            model_copy._build_and_calculate()

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

            self._model._build_and_calculate()

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
        value_format: ValueFormat = None,
    ) -> None:
        """
        Update a line item in the model by name.

        This method can update specific attributes of an existing line item or replace
        it entirely with a new LineItem instance. It validates the update by first
        testing it on a copy of the model, then applies the change to the actual model
        if successful.

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

        Examples:
            >>> # Update specific attributes
            >>> model.update.update_line_item("revenue", values={2023: 150000}, label="New Revenue")

            >>> # Rename a line item
            >>> model.update.update_line_item("old_name", new_name="new_name")

            >>> # Replace with a LineItem instance
            >>> model.update.update_line_item("revenue", line_item=new_line_item)
        """  # noqa: E501
        # Find the existing line item
        try:
            existing_item = self._model._line_item_definition(name)
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
                    category=category
                    if category is not None
                    else existing_item.category,
                    label=label if label is not None else existing_item.label,
                    values=values if values is not None else existing_item.values,
                    formula=formula if formula is not None else existing_item.formula,
                    value_format=value_format
                    if value_format is not None
                    else existing_item.value_format,
                )
            except ValueError as e:
                # Re-raise LineItem creation errors with our standard format
                raise ValueError(
                    f"Failed to update line item '{name}': {str(e)}"
                ) from e

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Find and replace the line item in the copy
            for i, item in enumerate(model_copy._line_item_definitions):
                if item.name == name:
                    model_copy._line_item_definitions[i] = updated_item
                    break
            model_copy._build_and_calculate()

            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            for i, item in enumerate(self._model._line_item_definitions):
                if item.name == name:
                    self._model._line_item_definitions[i] = updated_item
                    break
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update line item '{name}': {str(e)}") from e

    def update_multiple_line_items(
        self,
        item_updates: list[tuple[str, dict]],
    ) -> None:
        """
        Update multiple line items in a single operation.

        This method takes a list of tuples, where each tuple contains a line item name
        and a dictionary of parameters to update for that line item. It applies all updates
        in a single transaction, validating the entire set of changes before applying them.

        When using 'updated_values', the provided values are merged with existing values,
        rather than replacing them completely. To replace all values, use 'values' instead.
        Note: You cannot specify both 'values' and 'updated_values' for the same line item.

        Args:
            item_updates (list[tuple[str, dict]]): List of (name, update_params) tuples.
                Each tuple's first element is the line item name to update.
                Each tuple's second element is a dictionary of parameters to update,
                which can include: new_name, category, label, values, updated_values,
                formula, value_format.

        Returns:
            None

        Raises:
            ValueError: If any of the updates would result in an invalid model
            KeyError: If any line item name is not found in model

        Examples:
            >>> model.update.update_multiple_line_items([
            ...     # Replace all values
            ...     ("revenue", {"values": {2023: 150000}, "label": "New Revenue"}),
            ...
            ...     # Update only specific years (2023) while preserving other years
            ...     ("expenses", {"updated_values": {2023: 105000}, "formula": "revenue * 0.7"}),
            ...
            ...     # Only update formatting without touching values
            ...     ("profit", {"value_format": "percentage"})
            ... ])
        """  # noqa: E501
        if not item_updates:
            return

        # Helper function to apply updates to a model
        def apply_updates(model: "Model", updates: list[tuple[str, dict]]) -> None:
            for item_name, update_params in updates:
                # Find the existing line item
                existing_item = None
                for i, item in enumerate(model._line_item_definitions):
                    if item.name == item_name:
                        existing_item = item
                        item_index = i
                        break

                if existing_item is None:
                    raise KeyError(f"Line item '{item_name}' not found in model")

                # Create a working copy of the update parameters
                params_copy = update_params.copy()

                # Check for conflicting parameters: values and updated_values
                if "values" in params_copy and "updated_values" in params_copy:
                    raise ValueError(
                        f"Cannot specify both 'values' and 'updated_values' for line item '{item_name}'. "  # noqa: E501
                        f"Use 'values' to replace all values or 'updated_values' to update specific years."  # noqa: E501
                    )

                # Handle updated_values by merging with existing values
                if "updated_values" in params_copy:
                    merged_values = (
                        existing_item.values.copy()
                    )  # Start with existing values
                    merged_values.update(
                        params_copy["updated_values"]
                    )  # Update with new values
                    params_copy["values"] = merged_values

                    # Remove updated_values as it's not a LineItem parameter
                    del params_copy["updated_values"]

                # Create updated line item
                updated_item = LineItem(
                    name=params_copy.get("new_name", existing_item.name),
                    category=params_copy.get("category", existing_item.category),
                    label=params_copy.get("label", existing_item.label),
                    values=params_copy.get("values", existing_item.values),
                    formula=params_copy.get("formula", existing_item.formula),
                    value_format=params_copy.get(
                        "value_format", existing_item.value_format
                    ),
                )

                # Replace the existing item
                model._line_item_definitions[item_index] = updated_item

            # Recalculate the model with all changes
            model._build_and_calculate()

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            apply_updates(model_copy, item_updates)

            # If we get here, all updates were successful on the copy
            # Now apply them to the actual model
            apply_updates(self._model, item_updates)

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update line items: {str(e)}") from e

    def update_years(self, new_years: list[int]) -> None:
        """
        Update the years in the model.

        This method updates the model's years attribute and recalculates the value matrix
        for the new year range. It validates the update by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Line items with values for years not in the new list will retain those values,
        but they won't be accessible through the model until those years are added back.

        Args:
            new_years (list[int]): New list of years for the model

        Returns:
            None

        Raises:
            ValueError: If the years list is invalid (empty, non-integers, etc.)
            TypeError: If new_years is not a list

        Examples:
            >>> # Update years to a new range
            >>> model.update.update_years([2024, 2025, 2026])

            >>> # Extend years
            >>> model.update.update_years([2023, 2024, 2025, 2026, 2027])
        """  # noqa: E501
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
            model_copy._years = sorted(list(set(new_years)))
            model_copy._build_and_calculate()

            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            self._model._years = sorted(list(set(new_years)))
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update years: {str(e)}") from e

    def years(self, new_years: list[int]) -> None:
        """
        Convenience method to update years (alias for update_years).

        Args:
            new_years (list[int]): New list of years for the model

        Examples:
            >>> model.update.years([2024, 2025, 2026])
        """
        self.update_years(new_years)

    def reorder_line_items(self, ordered_names: list[str]) -> None:
        """
        Reorder LineItem definitions in the model by specifying their names in the desired order.

        This method reorders the LineItem class instances (line item definitions)
        based on the provided list of names. It only affects the order of LineItem
        objects in the model, not category totals, multi-line items, or other
        calculated items. All existing line items must be included in the list -
        no items can be omitted. The method validates the reordering by first
        testing it on a copy of the model, then applies the change to the actual
        model if successful.

        Args:
            ordered_names (list[str]): List of LineItem names in the desired order.
                Must contain all existing LineItem names, no more, no less.
                Only affects LineItem class instances, not other model components.

        Returns:
            None

        Raises:
            ValueError: If the reordering is invalid (missing items, extra items, etc.)
            TypeError: If ordered_names is not a list or contains non-strings

        Examples:
            >>> # Reorder LineItem definitions
            >>> model.update.reorder_line_items(["revenue", "expenses", "profit"])
        """  # noqa: E501
        # Input validation
        if not isinstance(ordered_names, list):
            raise TypeError(f"Expected list, got {type(ordered_names).__name__}")

        if not all(isinstance(name, str) for name in ordered_names):
            raise TypeError("All line item names must be strings")

        # Get current line item names
        current_names = [item.name for item in self._model._line_item_definitions]
        current_names_set = set(current_names)
        ordered_names_set = set(ordered_names)

        # Check for missing items
        missing_items = current_names_set - ordered_names_set
        if missing_items:
            raise ValueError(
                f"Missing line items in reorder list: {sorted(missing_items)}. "
                f"All existing line items must be included."
            )

        # Check for extra/unknown items
        unknown_items = ordered_names_set - current_names_set
        if unknown_items:
            available_items = sorted(current_names)
            raise ValueError(
                f"Unknown line items in reorder list: {sorted(unknown_items)}. "
                f"Available line items: {available_items}"
            )

        # Check for duplicates
        if len(ordered_names) != len(ordered_names_set):
            duplicates = [
                name for name in ordered_names if ordered_names.count(name) > 1
            ]
            raise ValueError(
                f"Duplicate line items in reorder list: {sorted(set(duplicates))}"
            )

        # If the order is already correct, no need to do anything
        if ordered_names == current_names:
            return

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()

            # Create a mapping from name to line item for efficient lookup
            name_to_item = {
                item.name: item for item in model_copy._line_item_definitions
            }

            # Reorder the line items according to the specified order
            reordered_items = [name_to_item[name] for name in ordered_names]
            model_copy._line_item_definitions = reordered_items

            model_copy._build_and_calculate()

            # If we get here, the reordering was successful on the copy
            # Now apply it to the actual model
            name_to_item = {
                item.name: item for item in self._model._line_item_definitions
            }
            reordered_items = [name_to_item[name] for name in ordered_names]
            self._model._line_item_definitions = reordered_items
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to reorder line items: {str(e)}") from e

    # ============================================================================
    # DELETE METHODS (formerly DeleteNamespace methods)
    # ============================================================================

    def delete_category(self, name: str, include_line_items: bool = False) -> None:
        """
        Delete a category from the model by name.

        This method validates the deletion by first testing it on a copy of
        the model, then applies the change to the actual model if successful.
        Note that deleting a category will fail if there are line items that
        reference this category, unless include_line_items is True.

        Args:
            name (str): Name of the category to delete
            include_line_items (bool): If True, delete all line items in this category
                                      before deleting the category. Defaults to False.

        Returns:
            None

        Raises:
            ValueError: If the category cannot be deleted (validation fails),
                       such as when line items still reference this category
                       and include_line_items is False
            KeyError: If the category with the given name is not found

        Examples:
            >>> model.update.delete_category("old_category")
            >>> model.update.delete_category("old_category", include_line_items=True)
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
        line_items_using_category = [
            item for item in self._model._line_item_definitions if item.category == name
        ]
        
        if line_items_using_category:
            if include_line_items:
                # Delete all line items in this category first
                item_names = [item.name for item in line_items_using_category]
                self.delete_line_items(item_names)
            else:
                # Fail if line items exist and we're not deleting them
                item_names = [item.name for item in line_items_using_category]
                raise ValueError(
                    f"Cannot delete category '{name}' because it is used by line items: {', '.join(item_names)}"  # noqa: E501
                )

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove the category from the copy
            model_copy._category_definitions = [
                category
                for category in model_copy._category_definitions
                if category.name != name
            ]
            model_copy._build_and_calculate()

            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model._category_definitions = [
                category
                for category in self._model._category_definitions
                if category.name != name
            ]
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete category '{name}': {str(e)}") from e

    def delete_line_item(self, name: str) -> None:
        """
        Delete a line item from the model by name.

        This method validates the deletion by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Args:
            name (str): Name of the line item to delete

        Returns:
            None

        Raises:
            ValueError: If the line item cannot be deleted (validation fails)
            KeyError: If the line item with the given name is not found

        Examples:
            >>> model.update.delete_line_item("expense_item")
        """
        # Verify the line item exists
        try:
            self._model._line_item_definition(name)
        except KeyError:
            raise KeyError(f"Line item '{name}' not found in model")

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove the line item from the copy
            model_copy._line_item_definitions = [
                item for item in model_copy._line_item_definitions if item.name != name
            ]
            model_copy._build_and_calculate()

            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model._line_item_definitions = [
                item for item in self._model._line_item_definitions if item.name != name
            ]
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete line item '{name}': {str(e)}") from e

    def delete_line_items(self, names: list[str]) -> None:
        """
        Delete multiple line items from the model by their names.

        This method validates the deletion by first testing it on a copy of
        the model, then applies the change to the actual model if successful.
        All line items are deleted in a single operation.

        Args:
            names (list[str]): List of line item names to delete

        Returns:
            None

        Raises:
            ValueError: If any line item cannot be deleted (validation fails)
            KeyError: If any line item with the given name is not found

        Examples:
            >>> model.update.delete_line_items(["expense_item", "revenue_item"])
        """
        # Verify all line items exist
        for name in names:
            try:
                self._model._line_item_definition(name)
            except KeyError:
                raise KeyError(f"Line item '{name}' not found in model")

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            # Remove all line items from the copy
            names_set = set(names)
            model_copy._line_item_definitions = [
                item for item in model_copy._line_item_definitions if item.name not in names_set
            ]
            model_copy._build_and_calculate()

            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model._line_item_definitions = [
                item for item in self._model._line_item_definitions if item.name not in names_set
            ]
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete line items {names}: {str(e)}") from e

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================

    def add_constraint(
        self,
        constraint: Constraint = None,
        *,
        name: str = None,
        line_item_name: str = None,
        target: float = None,
        operator: str = None,
        tolerance: float = 0.0,
        label: str = None,
    ) -> None:
        """
        Add a new constraint to the model.

        This method accepts either an already-created Constraint instance or the parameters
        to create a new one. It validates the addition by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Args:
            constraint (Constraint, optional): An already-created Constraint instance to add
            name (str, optional): Name for new Constraint - required if constraint is None
            line_item_name (str, optional): Name of line item this constraint applies to - required if constraint is None
            target (float, optional): Target value for constraint - required if constraint is None
            operator (str, optional): Comparison operator (eq, lt, le, gt, ge, ne) - required if constraint is None
            tolerance (float, optional): Tolerance for approximate comparisons. Defaults to 0.0
            label (str, optional): Display label for the constraint. Defaults to name if not provided

        Returns:
            None

        Raises:
            ValueError: If the constraint cannot be added (validation fails)
            TypeError: If neither constraint instance nor required parameters are provided

        Examples:
            >>> # Method 1: Pass a Constraint instance
            >>> model.update.add_constraint(existing_constraint)

            >>> # Method 2: Create from parameters
            >>> model.update.add_constraint(
            ...     name="revenue_min",
            ...     line_item_name="revenue",
            ...     target=50000.0,
            ...     operator="ge"
            ... )
        """  # noqa: E501
        if constraint is not None:
            # Method 1: Add an existing constraint
            new_constraint = constraint
        else:
            # Method 2: Create constraint from parameters
            if any(param is None for param in [name, line_item_name, target, operator]):
                raise ValueError(
                    "When constraint is None, name, line_item_name, target, and operator are required"  # noqa: E501
                )

            new_constraint = Constraint(
                name=name,
                line_item_name=line_item_name,
                target=target,
                operator=operator,
                tolerance=tolerance,
                label=label,
            )

        # Check if constraint name already exists
        existing_names = [c.name for c in self._model.constraints]
        if new_constraint.name in existing_names:
            raise ValueError(
                f"Constraint with name '{new_constraint.name}' already exists"
            )

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy.constraints.append(new_constraint)
            model_copy._build_and_calculate()

            # If we get here, the addition was successful on the copy
            # Now apply it to the actual model
            self._model.constraints.append(new_constraint)
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(
                f"Failed to add constraint '{new_constraint.name}': {str(e)}"
            ) from e

    def update_constraint(
        self,
        name: str,
        *,
        constraint: Constraint = None,
        new_name: str = None,
        line_item_name: str = None,
        target: float = None,
        operator: str = None,
        tolerance: float = None,
        label: str = None,
    ) -> None:
        """
        Update an existing constraint in the model.

        This method allows updating any aspect of an existing constraint. You can either
        provide a complete Constraint instance to replace the existing one, or provide
        specific parameters to update while keeping others unchanged.

        Args:
            name (str): Name of the existing constraint to update
            constraint (Constraint, optional): Complete constraint instance to replace existing one
            new_name (str, optional): New name for the constraint
            line_item_name (str, optional): New line item name for the constraint
            target (float, optional): New target value for the constraint
            operator (str, optional): New comparison operator for the constraint
            tolerance (float, optional): New tolerance for the constraint
            label (str, optional): New display label for the constraint

        Returns:
            None

        Raises:
            ValueError: If the constraint cannot be updated (validation fails)
            KeyError: If the constraint with the given name is not found

        Examples:
            >>> # Update specific parameters
            >>> model.update.update_constraint(
            ...     "revenue_min",
            ...     target=60000.0,
            ...     operator="gt"
            ... )

            >>> # Replace with new constraint instance
            >>> new_constraint = Constraint(name="revenue_min", ...)
            >>> model.update.update_constraint("revenue_min", constraint=new_constraint)
        """  # noqa: E501
        # Find the existing constraint
        constraint_index = None
        existing_constraint = None
        for i, c in enumerate(self._model.constraints):
            if c.name == name:
                constraint_index = i
                existing_constraint = c
                break

        if existing_constraint is None:
            available_constraints = [c.name for c in self._model.constraints]
            raise KeyError(
                f"Constraint '{name}' not found. Available constraints: {available_constraints}"  # noqa: E501
            )

        if constraint is not None:
            # Method 1: Replace with provided constraint
            updated_constraint = constraint
        else:
            # Method 2: Update specific parameters
            updated_constraint = Constraint(
                name=new_name if new_name is not None else existing_constraint.name,
                line_item_name=line_item_name
                if line_item_name is not None
                else existing_constraint.line_item_name,
                target=target if target is not None else existing_constraint.target,
                operator=operator
                if operator is not None
                else existing_constraint.operator,
                tolerance=tolerance
                if tolerance is not None
                else existing_constraint.tolerance,
                label=label if label is not None else existing_constraint.label,
            )

        # Check if new name conflicts with other constraints (excluding the one being updated)  # noqa: E501
        if updated_constraint.name != existing_constraint.name:
            existing_names = [
                c.name
                for c in self._model.constraints
                if c.name != existing_constraint.name
            ]
            if updated_constraint.name in existing_names:
                raise ValueError(
                    f"Constraint with name '{updated_constraint.name}' already exists"
                )

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy.constraints[constraint_index] = updated_constraint
            model_copy._build_and_calculate()

            # If we get here, the update was successful on the copy
            # Now apply it to the actual model
            self._model.constraints[constraint_index] = updated_constraint
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to update constraint '{name}': {str(e)}") from e

    def delete_constraint(self, name: str) -> None:
        """
        Delete a constraint from the model by name.

        This method validates the deletion by first testing it on a copy of
        the model, then applies the change to the actual model if successful.

        Args:
            name (str): Name of the constraint to delete

        Returns:
            None

        Raises:
            ValueError: If the constraint cannot be deleted (validation fails)
            KeyError: If the constraint with the given name is not found

        Examples:
            >>> model.update.delete_constraint("revenue_min")
        """
        # Verify the constraint exists
        constraint_exists = False
        for constraint in self._model.constraints:
            if constraint.name == name:
                constraint_exists = True
                break

        if not constraint_exists:
            available_constraints = [c.name for c in self._model.constraints]
            raise KeyError(
                f"Constraint '{name}' not found. Available constraints: {available_constraints}"  # noqa: E501
            )

        # Test on a copy of the model first
        try:
            model_copy = self._model.copy()
            model_copy.constraints = [
                c for c in model_copy.constraints if c.name != name
            ]
            model_copy._build_and_calculate()

            # If we get here, the deletion was successful on the copy
            # Now apply it to the actual model
            self._model.constraints = [
                c for c in self._model.constraints if c.name != name
            ]
            self._model._build_and_calculate()

        except Exception as e:
            # If validation fails, raise an informative error
            raise ValueError(f"Failed to delete constraint '{name}': {str(e)}") from e
