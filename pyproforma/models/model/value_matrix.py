"""
Value matrix generation for financial models.

This module contains the core calculation logic for generating the value matrix
that stores all calculated values for line items, categories, and generators
across all years in a financial model.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..line_item import LineItem
    from ..category import Category
    from pyproforma.models.line_item_generator import LineItemGenerator


def _calculate_category_total(
    values_by_name: dict[str, float], 
    line_item_metadata: list[dict],
    category_name: str
) -> float:
    """
    Calculate the sum of all line items in a category.
    
    This is an internal calculation method that computes the category total
    by summing all line item values in the specified category. Used during
    model initialization to populate the value matrix. None values are treated as 0.
    
    Args:
        values_by_name (dict): Dictionary mapping item names to their values
        line_item_metadata (list[dict]): Metadata for all defined names
        category_name (str): The name of the category to sum
        
    Returns:
        float: The calculated sum of all line items in the category
        
    Raises:
        KeyError: If the category name is not found in metadata or if line items 
                 in the category are not found in values
    """
    # Check if the category exists in metadata
    category_exists = any(
        metadata.get('source_type') == 'line_item' and metadata.get('category') == category_name
        for metadata in line_item_metadata
    )
    if not category_exists:
        available_categories = set(
            metadata.get('category') for metadata in line_item_metadata
            if metadata.get('source_type') == 'line_item' and metadata.get('category') is not None
        )
        raise KeyError(f"Category '{category_name}' not found in metadata. Available categories: {sorted(available_categories)}")
    
    # Find all line items that belong to this category and sum their values
    total = 0
    for metadata in line_item_metadata:
        if metadata['source_type'] == 'line_item' and metadata['category'] == category_name:
            item_name = metadata['name']
            if item_name not in values_by_name:
                raise KeyError(f"Line item '{item_name}' in category '{category_name}' not found in values")
            
            value = values_by_name[item_name]
            if value is not None:
                total += value
    
    return total


def generate_value_matrix(
    years: list[int],
    line_item_definitions: list["LineItem"],
    line_item_generators: list["LineItemGenerator"],
    category_definitions: list["Category"],
    line_item_metadata: list[dict]
) -> dict[int, dict[str, float]]:
    """
    Generate the value matrix containing all calculated values for the model.
    
    This function calculates all line item values, line item generator outputs,
    and category totals for each year in the model. It handles dependency resolution
    by calculating items in the correct order based on formula dependencies.
    
    Args:
        years (list[int]): List of years in the model
        line_item_definitions (list[LineItem]): List of line item definitions
        line_item_generators (list[LineItemGenerator]): List of line item generators
        category_definitions (list[Category]): List of category definitions  
        line_item_metadata (list[dict]): Metadata for all defined names
        
    Returns:
        dict[int, dict[str, float]]: Nested dictionary with years as keys and
            item names as inner keys, containing all calculated values
            
    Raises:
        ValueError: If circular dependencies are detected or items cannot be calculated
        KeyError: If defined names are missing from the value matrix
    """
    value_matrix = {}
    for year in years:
        value_matrix[year] = {}
    
        # Calculate line items in dependency order
        calculated_items = set()
        remaining_items = line_item_definitions.copy()
        max_iterations = len(line_item_definitions) + 1  # Safety valve
        iteration = 0
        
        # Track which line item generators have been successfully calculated
        remaining_generators = line_item_generators.copy() if line_item_generators else []
        
        while (remaining_items or remaining_generators) and iteration < max_iterations:
            iteration += 1
            items_calculated_this_round = []
            generators_calculated_this_round = []
            
            # Try to calculate line item generators for this year
            for generator in remaining_generators:
                try:
                    # Try to calculate values for this line item generator
                    generated_values = generator.get_values(value_matrix, year)
                    
                    # Update value matrix with the generated values
                    value_matrix[year].update(generated_values)
                    
                    # Mark this generator as calculated
                    generators_calculated_this_round.append(generator)
                except (KeyError, ValueError):
                    # Skip if dependencies are not yet met
                    # Will try again in the next iteration
                    continue
            
            # Remove successfully calculated generators from remaining list
            for generator in generators_calculated_this_round:
                remaining_generators.remove(generator)
            
            for item in remaining_items:
                try:
                    # Try to calculate the item
                    value_matrix[year][item.name] = item.get_value(value_matrix, year)
                    calculated_items.add(item.name)
                    items_calculated_this_round.append(item)
                            
                except (KeyError, ValueError) as e:
                    # Check if this is a None value error - these should be raised immediately
                    if isinstance(e, ValueError) and "has None value" in str(e) and "Cannot use None values in formulas" in str(e):
                        raise e
                    
                    # Check if this is a missing variable error vs dependency issue
                    if isinstance(e, ValueError) and "not found for year" in str(e):
                        # Extract variable name from error message
                        import re as error_re
                        match = error_re.search(r"Variable '(\w+)' not found for year", str(e))
                        if match:
                            var_name = match.group(1)
                            # Check if this variable exists in our defined names
                            all_defined_names = [name['name'] for name in line_item_metadata]
                            if var_name not in all_defined_names:
                                # Variable truly doesn't exist, create enhanced error message
                                raise ValueError(f"Error calculating line item '{item.name}' for year {year}. Formula: '{item.formula}'. Line item '{var_name}' not found in model.") from e
                    # Item depends on something not yet calculated, skip for now
                    continue
        
            # Remove successfully calculated items from remaining list
            for item in items_calculated_this_round:
                remaining_items.remove(item)
            
            # After each round, check if we can calculate any category totals
            for category in category_definitions:
                if category.include_total and category.total_name not in value_matrix[year]:
                    # Check if all items in this category have been calculated
                    items_in_category = [item for item in line_item_definitions if item.category == category.name]
                    all_items_calculated = all(item.name in calculated_items for item in items_in_category)
                    
                    if all_items_calculated and items_in_category:  # Only if category has items
                        category_total = _calculate_category_total(
                            value_matrix[year], line_item_metadata, category.name
                        )
                        total_name = category.total_name
                        value_matrix[year][total_name] = category_total
            
            # If no progress was made this round, we have circular dependencies
            if not items_calculated_this_round and not generators_calculated_this_round:
                break
        
        # Check if all items and generators were calculated
        errors = []
        if remaining_items:
            failed_items = [item.name for item in remaining_items]
            errors.append(f"Could not calculate line items due to missing dependencies or circular references: {failed_items}")
            
        if remaining_generators:
            failed_generators = [generator.name for generator in remaining_generators]
            errors.append(f"Could not calculate line item generators due to missing dependencies or circular references: {failed_generators}")
            
        if errors:
            raise ValueError("\n".join(errors))
    
        # Ensure all defined names are present in the value matrix
        for name in line_item_metadata:
            if name['name'] not in value_matrix[year]:
                raise KeyError(f"Defined name '{name['name']}' not found in value matrix for year {year}.")

    return value_matrix
