"""
Value matrix generation for financial models.

This module contains the core calculation logic for generating the value matrix
that stores all calculated values for line items, categories, and generators
across all years in a financial model.
"""

from typing import TYPE_CHECKING, Any, Dict, Union

from ..formula import calculate_formula

if TYPE_CHECKING:
    from pyproforma.models.multi_line_item import MultiLineItem

    from ..category import Category
    from ..line_item import LineItem


class ValueMatrixValidationError(Exception):
    """Raised when value matrix validation fails."""

    pass


def validate_value_matrix(
    values_by_year: Dict[int, Dict[str, Any]],
) -> None:
    """
    Validates a dictionary of interim values organized by year.

    Requirements:
    - Keys must be years (integers) and in ascending order
    - Values must be dictionaries mapping variable names to values
    - All years except the last must contain the same set of variables
    - The last year may contain a subset of the variables from previous years

    Args:
        values_by_year (Dict[int, Dict[str, Any]]): Dictionary mapping years to value dictionaries  # noqa: E501

    Raises:
        ValueMatrixValidationError: If the structure is invalid
    """  # noqa: E501
    if not values_by_year:
        return  # Empty dict is valid

    # Check if keys are years and in ascending order
    years = list(values_by_year.keys())
    if not all(isinstance(year, int) for year in years):
        raise ValueMatrixValidationError("All keys must be integers representing years")

    sorted_years = sorted(years)
    if sorted_years != years:
        raise ValueMatrixValidationError("Years must be in ascending order")

    # Check if all values are dictionaries
    non_dict_years = [
        year for year in years if not isinstance(values_by_year[year], dict)
    ]
    if non_dict_years:
        raise ValueMatrixValidationError(
            f"Values for years {non_dict_years} must be dictionaries"
        )

    # If there's only one year, nothing more to check
    if len(years) <= 1:
        return

    # Get the set of variable names from the first year
    reference_year = years[0]
    reference_names = set(values_by_year[reference_year].keys())

    # Check that all years except the last one have the same variable names
    for year in years[1:-1]:
        current_names = set(values_by_year[year].keys())
        if current_names != reference_names:
            missing = reference_names - current_names
            extra = current_names - reference_names
            error_msg = f"Year {year} has inconsistent variable names with the first year ({reference_year})"  # noqa: E501
            if missing:
                error_msg += f", missing: {', '.join(missing)}"
            if extra:
                error_msg += f", extra: {', '.join(extra)}"
            raise ValueMatrixValidationError(error_msg)

    # Check that the last year only has keys that are within the reference set
    last_year = years[-1]
    last_year_names = set(values_by_year[last_year].keys())
    extra_keys = last_year_names - reference_names
    if extra_keys:
        raise ValueMatrixValidationError(
            f"Last year ({last_year}) contains extra variables not present in previous years: {', '.join(extra_keys)}"  # noqa: E501
        )


def calculate_line_item_value(
    hardcoded_values: dict[int, float | None],
    formula: str | None,
    interim_values_by_year: dict,
    year: int,
    name: str,
) -> float | None:
    """
    Calculate the value for a line item in a specific year.

    The function follows this precedence:
    1. Check if value already exists in interim_values_by_year (raises error if found)
    2. Return explicit value from hardcoded_values if available for the year and not None
    3. Calculate value using formula if formula is defined (used when hardcoded value is None or missing)
    4. Return None if no value or formula is available

    Args:
        hardcoded_values (dict[int, float | None]): Dictionary mapping years to explicit values.
            None values will be ignored and formulas will be used instead.
        formula (str | None): Formula string for calculating values when explicit
            values are not available or are None.
        interim_values_by_year (dict): Dictionary containing calculated values
            by year, used to prevent circular references and for formula calculations.
        year (int): The year for which to get the value.
        name (str): The name of the line item (used for error messages and duplicate checking).

    Returns:
        float or None: The calculated/stored value for the specified year, or None if no value/formula exists.

    Raises:
        ValueError: If value already exists in interim_values_by_year or if interim_values_by_year is invalid.
    """  # noqa: E501
    # Validate interim values by year
    validate_value_matrix(interim_values_by_year)

    # If interim_values_by_year[year][name] already exists, raise an error
    if year in interim_values_by_year and name in interim_values_by_year[year]:
        raise ValueError(
            f"Value for {name} in year {year} already exists in interim values."
        )

    # If value for this year is in hardcoded_values and is not None, return that value
    if year in hardcoded_values and hardcoded_values[year] is not None:
        return hardcoded_values[year]

    # If no explicit value (missing key or None value), use formula
    if formula:
        return calculate_formula(formula, interim_values_by_year, year)
    # If no formula is defined, return None
    return None


def _calculate_category_total(
    values_by_name: dict[str, float], line_item_metadata: list[dict], category_name: str
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
        metadata.get("source_type") == "line_item"
        and metadata.get("category") == category_name
        for metadata in line_item_metadata
    )
    if not category_exists:
        available_categories = set(
            metadata.get("category")
            for metadata in line_item_metadata
            if metadata.get("source_type") == "line_item"
            and metadata.get("category") is not None
        )
        raise KeyError(
            f"Category '{category_name}' not found in metadata. Available categories: {sorted(available_categories)}"  # noqa: E501
        )

    # Find all line items that belong to this category and sum their values
    total = 0
    for metadata in line_item_metadata:
        if (
            metadata["source_type"] == "line_item"
            and metadata["category"] == category_name
        ):
            item_name = metadata["name"]
            if item_name not in values_by_name:
                raise KeyError(
                    f"Line item '{item_name}' in category '{category_name}' not found in values"  # noqa: E501
                )

            value = values_by_name[item_name]
            if value is not None:
                total += value

    return total


def generate_value_matrix(
    years: list[int],
    line_item_definitions: list[Union["LineItem", "MultiLineItem"]],
    category_definitions: list["Category"],
    line_item_metadata: list[dict],
) -> dict[int, dict[str, float]]:
    """
    Generate the value matrix containing all calculated values for the model.

    This function calculates all line item values, multi line item outputs,
    and category totals for each year in the model. It handles dependency resolution
    by calculating items in the correct order based on formula dependencies.

    Args:
        years (list[int]): List of years in the model
        line_item_definitions (list[Union[LineItem, MultiLineItem]]): List of line item definitions and multi line items  # noqa: E501
        category_definitions (list[Category]): List of category definitions
        line_item_metadata (list[dict]): Metadata for all defined names

    Returns:
        dict[int, dict[str, float]]: Nested dictionary with years as keys and
            item names as inner keys, containing all calculated values

    Raises:
        ValueError: If circular dependencies are detected or items cannot be calculated
        KeyError: If defined names are missing from the value matrix
    """  # noqa: E501
    value_matrix = {}
    for year in years:
        value_matrix[year] = {}

        # Calculate line items in dependency order
        calculated_items = set()
        remaining_items = line_item_definitions.copy()
        max_iterations = len(line_item_definitions) + 1  # Safety valve
        iteration = 0

        while remaining_items and iteration < max_iterations:
            iteration += 1
            items_calculated_this_round = []

            for item in remaining_items:
                try:
                    # Check if this is a MultiLineItem or LineItem
                    # MultiLineItems have get_values() and defined_names, LineItems have name attribute  # noqa: E501

                    if hasattr(item, "get_values") and hasattr(item, "defined_names"):
                        # Handle MultiLineItem - get multiple values
                        generated_values = item.get_values(value_matrix, year)

                        # Update value matrix with the generated values
                        value_matrix[year].update(generated_values)

                        # Add all generated names to calculated_items
                        calculated_items.update(generated_values.keys())

                        # Mark this generator as calculated
                        items_calculated_this_round.append(item)
                    elif hasattr(item, "name"):
                        li_metadata = next(
                            metadata
                            for metadata in line_item_metadata
                            if metadata["name"] == item.name
                        )
                        # Handle LineItem - get single value
                        value_matrix[year][item.name] = calculate_line_item_value(
                            li_metadata["hardcoded_values"],
                            item.formula,
                            value_matrix,
                            year,
                            item.name,
                        )
                        calculated_items.add(item.name)
                        items_calculated_this_round.append(item)
                    else:
                        # Unknown object type, skip
                        raise ValueError(f"Unknown item type: {type(item)}")

                except (KeyError, ValueError) as e:
                    # Check if this is a None value error - these should be raised immediately  # noqa: E501
                    if (
                        isinstance(e, ValueError)
                        and "has None value" in str(e)
                        and "Cannot use None values in formulas" in str(e)
                    ):
                        raise e

                    # Check if this is a missing variable error vs dependency issue
                    if isinstance(e, ValueError) and "not found for year" in str(e):
                        # Extract variable name from error message
                        import re as error_re

                        match = error_re.search(
                            r"Variable '(\w+)' not found for year", str(e)
                        )
                        if match:
                            var_name = match.group(1)
                            # Check if this variable exists in our defined names
                            all_defined_names = [
                                name["name"] for name in line_item_metadata
                            ]
                            if var_name not in all_defined_names:
                                # Variable truly doesn't exist, create enhanced error message  # noqa: E501
                                item_name = getattr(item, "name", str(item))
                                formula = getattr(item, "formula", "N/A")
                                raise ValueError(
                                    f"Error calculating line item '{item_name}' for year {year}. Formula: '{formula}'. Line item '{var_name}' not found in model."  # noqa: E501
                                ) from e
                    # Item depends on something not yet calculated, skip for now
                    continue

            # Remove successfully calculated items from remaining list
            for item in items_calculated_this_round:
                remaining_items.remove(item)

            # After each round, check if we can calculate any category totals
            for category in category_definitions:
                if (
                    category.include_total
                    and category.total_name not in value_matrix[year]
                ):
                    # Check if all items in this category have been calculated
                    # Only look at LineItem objects for category totals, not MultiLineItems  # noqa: E501
                    line_items_only = [
                        item
                        for item in line_item_definitions
                        if hasattr(item, "name") and not hasattr(item, "defined_names")
                    ]
                    items_in_category = [
                        item
                        for item in line_items_only
                        if item.category == category.name
                    ]
                    all_items_calculated = all(
                        item.name in calculated_items for item in items_in_category
                    )

                    if (
                        all_items_calculated and items_in_category
                    ):  # Only if category has items
                        category_total = _calculate_category_total(
                            value_matrix[year], line_item_metadata, category.name
                        )
                        total_name = category.total_name
                        value_matrix[year][total_name] = category_total

            # If no progress was made this round, we have circular dependencies
            if not items_calculated_this_round:
                break

        # Check if all items were calculated
        if remaining_items:
            failed_items = []
            for item in remaining_items:
                if hasattr(item, "get_values") and hasattr(item, "defined_names"):
                    # MultiLineItem
                    failed_items.extend(
                        item.defined_names
                    )  # Add all names from the generator
                elif hasattr(item, "name") and not hasattr(item, "defined_names"):
                    # LineItem
                    failed_items.append(item.name)  # Add the single line item name
                else:
                    # Unknown type
                    failed_items.append(str(item))

            raise ValueError(
                f"Could not calculate line items due to missing dependencies or circular references: {failed_items}"  # noqa: E501
            )

        # Ensure all defined names are present in the value matrix
        for name in line_item_metadata:
            if name["name"] not in value_matrix[year]:
                raise KeyError(
                    f"Defined name '{name['name']}' not found in value matrix for year {year}."  # noqa: E501
                )

    return value_matrix
