"""
Metadata collection utilities for model components.

This module provides functions to collect and structure metadata from various
model components including categories and line items.
"""

from typing import Dict, List

from pyproforma.constants import CONSTRAINT_OPERATOR_SYMBOLS
from pyproforma.models.generator import Generator

from ..category import Category
from ..constraint import Constraint
from ..line_item import LineItem


def generate_category_metadata(
    category_definitions: List[Category], generators: List[Generator] = None
) -> List[Dict]:
    """
    Collect category metadata from category definitions and generators.

    This function extracts key information from each category definition
    to create a comprehensive metadata structure for categories, and also
    creates category metadata entries for generators (without creating
    actual Category objects for them).

    Args:
        category_definitions (List[Category]): List of category definitions
        generators (List[Generator], optional): List of generator
            objects

    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The category name
            - 'label' (str): The display label for the category
            - 'system_generated' (bool): Whether this is a system-generated category
    """
    category_metadata = []

    # Add metadata for category definitions
    for category in category_definitions:
        label = category.label if category.label is not None else category.name

        category_metadata.append(
            {
                "name": category.name,
                "label": label,
                "system_generated": False,
            }
        )

    # Add metadata for generators (as system-generated categories)
    if generators is not None:
        existing_category_names = {cat["name"] for cat in category_metadata}
        for generator in generators:
            if generator.name not in existing_category_names:
                category_metadata.append(
                    {
                        "name": generator.name,
                        "label": f"{generator.name} (Generator)",
                        "system_generated": True,
                    }
                )

    return category_metadata


def generate_line_item_metadata(
    line_item_definitions: List[LineItem],
    category_metadata: List[Dict],
    generators: List[Generator],
) -> List[Dict]:
    """
    Collects all defined names across the model to create a comprehensive
    namespace.

    This function aggregates identifiers from all model components including
    line items and generators to build a unified namespace for
    value lookups and validation.

    Args:
        line_item_definitions (List[LineItem]): List of line item definitions
        category_metadata (List[Dict]): List of category metadata dictionaries
        generators (List[Generator]): List of generator objects

    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The identifier name used for lookups
            - 'label' (str): The display label for this identifier
            - 'value_format' (str): The formatting type for values
              (None, 'str', 'no_decimals', 'two_decimals', 'percent',
              'percent_one_decimal', 'percent_two_decimals')
            - 'source_type' (str): The component type that defines this name
              ('line_item', 'generator')
            - 'source_name' (str): The original source object's name
            - 'category' (str): The category name
            - 'formula' (str or None): The formula string for line items
              (None for other types)
            - 'hardcoded_values' (dict or None): Dictionary of year->value
              mappings for line items (None for other types)

    Raises:
        ValueError: If duplicate names are found across different components

    Example:
        For a model with revenue line item:
        [
            {'name': 'revenue', 'label': 'Revenue',
             'value_format': 'no_decimals', 'source_type': 'line_item',
             'source_name': 'revenue', 'category': 'income',
             'formula': 'sales * price', 'hardcoded_values': {2023: 100000}}
        ]
    """
    defined_names = []

    # Add line item definitions
    for item in line_item_definitions:
        # If label is None, use name as label
        label = item.label if item.label is not None else item.name

        # If hardcoded values are None, use {}
        hardcoded_values = item.values if item.values is not None else {}

        defined_names.append(
            {
                "name": item.name,
                "label": label,
                "value_format": item.value_format,
                "source_type": "line_item",
                "source_name": item.name,
                "category": item.category,
                "formula": item.formula,
                "hardcoded_values": hardcoded_values,
            }
        )

    # Add generators
    for generator in generators:
        for gen_name in generator.defined_names:
            defined_names.append(
                {
                    "name": gen_name,
                    "label": gen_name,
                    "value_format": "no_decimals",
                    "source_type": "generator",
                    "source_name": generator.name,
                    "category": generator.name,
                    "formula": None,
                    "hardcoded_values": None,
                }
            )

    # Check for duplicate names in defined_names
    # and raise ValueError if any duplicates are found.
    names_list = [item["name"] for item in defined_names]
    duplicates = set([name for name in names_list if names_list.count(name) > 1])
    if duplicates:
        raise ValueError(
            f"Duplicate defined names found in Model: {', '.join(duplicates)}"
        )
    return defined_names


def generate_constraint_metadata(constraints: List[Constraint]) -> List[Dict]:
    """
    Collect constraint metadata from constraint definitions.

    This function extracts key information from each constraint definition
    to create a comprehensive metadata structure for constraints.

    Args:
        constraints (List[Constraint]): List of constraint definitions

    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The constraint name
            - 'label' (str): The display label for the constraint
            - 'line_item_name' (str): The name of the line item being constrained
            - 'target' (Union[float, Dict[int, float]]): The target value(s) for
              comparison
            - 'operator' (str): The comparison operator ('eq', 'lt', 'le', 'gt',
              'ge', 'ne')
            - 'operator_symbol' (str): The symbol representation of the operator
              ('=', '<', etc.)
            - 'tolerance' (float): The tolerance for approximate comparisons
    """
    constraint_metadata = []

    for constraint in constraints:
        label = constraint.label if constraint.label is not None else constraint.name
        constraint_metadata.append(
            {
                "name": constraint.name,
                "label": label,
                "line_item_name": constraint.line_item_name,
                "target": constraint.target,
                "operator": constraint.operator,
                "operator_symbol": CONSTRAINT_OPERATOR_SYMBOLS[constraint.operator],
                "tolerance": constraint.tolerance,
            }
        )

    return constraint_metadata
