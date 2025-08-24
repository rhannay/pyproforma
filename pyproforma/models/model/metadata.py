"""
Metadata collection utilities for model components.

This module provides functions to collect and structure metadata from various
model components including categories and line items.
"""

from typing import List, Dict
from ..line_item import LineItem
from ..category import Category
from pyproforma.models.multi_line_item import MultiLineItem


def collect_category_metadata(
    category_definitions: List[Category],
    multi_line_items: List[MultiLineItem] = None
) -> List[Dict]:
    """
    Collect category metadata from category definitions and multi-line items.
    
    This function extracts key information from each category definition
    to create a comprehensive metadata structure for categories, and also
    creates category metadata entries for multi-line items (without creating
    actual Category objects for them).
    
    Args:
        category_definitions (List[Category]): List of category definitions
        multi_line_items (List[MultiLineItem], optional): List of multi-line item generators
    
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The category name
            - 'label' (str): The display label for the category
            - 'include_total' (bool): Whether the category includes a total row
            - 'total_name' (str): The name used for the category total
            - 'total_label' (str): The display label for the category total
            - 'system_generated' (bool): Whether this is a system-generated category
    """
    category_metadata = []
    
    # Add metadata for category definitions
    for category in category_definitions:
        category_metadata.append({
            'name': category.name,
            'label': category.label,
            'include_total': category.include_total,
            'total_name': category.total_name,
            'total_label': category.total_label,
            'system_generated': False
        })
    
    # Add metadata for multi-line items (as system-generated categories)
    if multi_line_items is not None:
        existing_category_names = {cat['name'] for cat in category_metadata}
        for multi_item in multi_line_items:
            if multi_item.name not in existing_category_names:
                category_metadata.append({
                    'name': multi_item.name,
                    'label': f'{multi_item.name} (Multi-Line Item)',
                    'include_total': False,
                    'total_name': None,
                    'total_label': None,
                    'system_generated': True
                })
    
    # Add 'category_totals' category if any categories have totals
    categories_with_totals = [cat for cat in category_metadata if cat['include_total']]
    if categories_with_totals:
        category_metadata.append({
            'name': 'category_totals',
            'label': 'Category Totals',
            'include_total': False,
            'total_name': None,
            'total_label': None,
            'system_generated': True
        })
    
    return category_metadata


def collect_line_item_metadata(
    line_item_definitions: List[LineItem],
    category_metadata: List[Dict],
    multi_line_items: List[MultiLineItem]
) -> List[Dict]:
    """
    Collects all defined names across the model to create a comprehensive 
    namespace.
    
    This function aggregates identifiers from all model components including 
    line items, category totals, and line item generators to 
    build a unified namespace for value lookups and validation.
    
    Args:
        line_item_definitions (List[LineItem]): List of line item definitions
        category_metadata (List[Dict]): List of category metadata dictionaries
        multi_line_items (List[MultiLineItem]): List of multi-line item generators
    
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - 'name' (str): The identifier name used for lookups
            - 'label' (str): The display label for this identifier
            - 'value_format' (str): The formatting type for values 
              (None, 'str', 'no_decimals', 'two_decimals', 'percent', 
              'percent_one_decimal', 'percent_two_decimals')
            - 'source_type' (str): The component type that defines this name
              ('line_item', 'category', 'multi_line_item')
            - 'source_name' (str): The original source object's name
            - 'category' (str): The category name
            
    Raises:
        ValueError: If duplicate names are found across different components
                   
    Example:
        For a model with revenue line item and revenue category:
        [
            {'name': 'revenue', 'label': 'Revenue', 
             'value_format': 'no_decimals', 'source_type': 'line_item', 
             'source_name': 'revenue', 'category': 'income'},
            {'name': 'total_revenue', 'label': 'Total Revenue', 
             'value_format': 'no_decimals', 'source_type': 'category', 
             'source_name': 'revenue', 'category': 'category_totals'}
        ]
    """
    defined_names = []
    
    # Add line item definitions
    for item in line_item_definitions:
        defined_names.append({
            'name': item.name, 
            'label': item.label, 
            'value_format': item.value_format, 
            'source_type': 'line_item', 
            'source_name': item.name,
            'category': item.category,
        })
    
    # Add category totals from metadata
    for category_meta in category_metadata:
        if category_meta['include_total']:
            # Only include category total if there are line items in category
            items_in_category = [
                item for item in line_item_definitions 
                if item.category == category_meta['name']
            ]
            if items_in_category:  # Only add total if category has items
                defined_names.append({
                    'name': category_meta['total_name'], 
                    'label': category_meta['total_label'], 
                    'value_format': 'no_decimals', 
                    'source_type': 'category', 
                    'source_name': category_meta['name'],
                    'category': 'category_totals',
                })
    
    # Add multi-line item generators
    for generator in multi_line_items:
        for gen_name in generator.defined_names:
            defined_names.append({
                'name': gen_name, 
                'label': gen_name, 
                'value_format': 'no_decimals', 
                'source_type': 'multi_line_item', 
                'source_name': generator.name,
                'category': generator.name,
            })
    
    # Check for duplicate names in defined_names
    # and raise ValueError if any duplicates are found.
    names_list = [item['name'] for item in defined_names]
    duplicates = set([
        name for name in names_list if names_list.count(name) > 1
    ])
    if duplicates:
        raise ValueError(
            f"Duplicate defined names found in Model: {', '.join(duplicates)}"
        )
    return defined_names
