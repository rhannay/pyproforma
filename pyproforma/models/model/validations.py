"""
Validation functions for model components.

This module contains validation logic for model components including
categories, constraints, multi line items, and formulas.
"""

from typing import List

from pyproforma.models.multi_line_item import MultiLineItem

from ..category import Category
from ..constraint import Constraint
from ..formula import validate_formula
from ..line_item import LineItem


def validate_line_items(line_items: List[LineItem], categories: List[Category]):
    """
    Validates that all line items have unique names and reference valid categories.

    Args:
        line_items (List[LineItem]): List of line items to validate
        categories (List[Category]): List of category definitions to validate references against  # noqa: E501

    Raises:
        ValueError: If two or more line items have the same name, or if a line item
                   references a category that is not defined.
    """  # noqa: E501
    if not line_items:
        return

    line_item_names = [item.name for item in line_items]
    duplicates = set(
        [name for name in line_item_names if line_item_names.count(name) > 1]
    )

    if duplicates:
        raise ValueError(
            f"Duplicate line item names not allowed: {', '.join(sorted(duplicates))}"
        )

    # Validate that all item types in line_items are defined in categories
    category_names = [category.name for category in categories]
    for item in line_items:
        if item.category not in category_names:
            raise ValueError(
                f"Category '{item.category}' for LineItem '{item.name}' is not defined category."  # noqa: E501
            )


def validate_categories(categories: List[Category]):
    """
    Validates that all category names are unique.

    Args:
        categories (List[Category]): List of category definitions

    Raises:
        ValueError: If duplicate category names are found.
    """
    # Validate that all category names are unique
    category_names = [category.name for category in categories]
    duplicates = set(
        [name for name in category_names if category_names.count(name) > 1]
    )

    if duplicates:
        raise ValueError(
            f"Duplicate category names not allowed: {', '.join(sorted(duplicates))}"
        )


def validate_constraints(constraints: List[Constraint], line_items: List[LineItem]):
    """
    Validates that all constraints have unique names and reference existing line items.

    Args:
        constraints (List[Constraint]): List of constraints to validate
        line_items (List[LineItem]): List of line items for reference validation

    Raises:
        ValueError: If two or more constraints have the same name, or if a constraint
                   references a line item that doesn't exist.
    """
    if not constraints:
        return

    constraint_names = [constraint.name for constraint in constraints]
    duplicates = set(
        [name for name in constraint_names if constraint_names.count(name) > 1]
    )

    if duplicates:
        raise ValueError(
            f"Duplicate constraint names not allowed: {', '.join(sorted(duplicates))}"
        )

    # Validate that all constraint line_item_names reference existing line items
    line_item_names = [item.name for item in line_items]
    for constraint in constraints:
        if constraint.line_item_name not in line_item_names:
            raise ValueError(
                f"Constraint '{constraint.name}' references unknown line item '{constraint.line_item_name}'"  # noqa: E501
            )


def validate_multi_line_items(
    multi_line_items: List[MultiLineItem], categories: List[Category]
):
    """
    Validates that all multi line items have unique names and don't conflict with category names.  # noqa: E501

    Args:
        multi_line_items (List[MultiLineItem]): List of multi line items to validate
        categories (List[Category]): List of categories to check for name conflicts

    Raises:
        ValueError: If two or more multi line items have the same name, or if a multi
                   line item name conflicts with a category name.
    """  # noqa: E501
    if not multi_line_items:
        return

    generator_names = [generator.name for generator in multi_line_items]
    duplicates = set(
        [name for name in generator_names if generator_names.count(name) > 1]
    )

    if duplicates:
        raise ValueError(
            f"Duplicate multi line item names not allowed: {', '.join(sorted(duplicates))}"  # noqa: E501
        )

    # Validate that multi line item names don't conflict with category names
    category_names = [category.name for category in categories]
    conflicts = [name for name in generator_names if name in category_names]

    if conflicts:
        raise ValueError(
            f"Multi line item names cannot match category names: {', '.join(sorted(conflicts))}"  # noqa: E501
        )


def validate_formulas(line_items: List[LineItem], line_item_metadata: List[dict]):
    """
    Validates that all line item formulas reference only defined variables.

    This method checks each line item that has a formula to ensure all variables
    referenced in the formula exist in the model's defined names. This includes
    line items, category totals, and line item generator outputs.

    Args:
        line_items (List[LineItem]): List of line items to validate
        line_item_metadata (List[dict]): List of metadata dictionaries containing defined names  # noqa: E501

    Raises:
        ValueError: If any formula contains undefined variable names
    """  # noqa: E501
    if not line_items:
        return

    # Get all defined names that can be used in formulas
    defined_variable_names = [name["name"] for name in line_item_metadata]

    # Validate each line item's formula
    for line_item in line_items:
        if line_item.formula is not None and line_item.formula.strip():
            try:
                validate_formula(
                    line_item.formula, line_item.name, defined_variable_names
                )
            except ValueError as e:
                # Enhance the error message to include the line item name
                raise ValueError(
                    f"Error in formula for line item '{line_item.name}': {str(e)}"
                ) from e


def validate_years(years: List[int]):
    """
    Validates that years are integers, sequential, sorted, and have no gaps.

    Args:
        years (List[int]): List of years to validate

    Raises:
        ValueError: If years are not integers, not sorted, not sequential, or have gaps.
        TypeError: If years is None.
    """
    if years is None:
        raise TypeError("Years cannot be None")

    if not years:
        return  # Empty years list is allowed for template models

    # Check that all years are integers
    for year in years:
        if not isinstance(year, int):
            raise ValueError(
                f"All years must be integers, found: {year} ({type(year).__name__})"
            )

    # Check that years are sorted
    if years != sorted(years):
        raise ValueError(f"Years must be in ascending order: {years}")

    # Check that years are sequential with no gaps
    if len(years) > 1:
        for i in range(1, len(years)):
            if years[i] != years[i - 1] + 1:
                raise ValueError(
                    f"Years must be sequential with no gaps. "
                    f"Gap found between {years[i - 1]} and {years[i]}"
                )
