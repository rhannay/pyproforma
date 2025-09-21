"""
Metadata collection utilities for model components.

This module provides functions to collect and structure metadata from various
model components including categories, line items, and constraints.
"""

from .metadata import (
    generate_category_metadata,
    generate_constraint_metadata,
    generate_line_item_metadata,
)

__all__ = [
    "generate_category_metadata",
    "generate_constraint_metadata",
    "generate_line_item_metadata",
]
