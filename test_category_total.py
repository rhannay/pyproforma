#!/usr/bin/env python3
"""
Test script to verify that _calculate_category_total now requires category_metadata.
"""

from pyproforma.models.model.value_matrix import _calculate_category_total


def test_category_metadata_required():
    """Test that category_metadata is now required."""

    # Test data
    values_by_name = {"revenue1": 1000.0, "revenue2": 500.0}
    line_item_metadata = [
        {"name": "revenue1", "source_type": "line_item", "category": "income"},
        {"name": "revenue2", "source_type": "line_item", "category": "income"},
    ]
    category_metadata = [{"name": "income"}]

    # This should work with category_metadata
    result = _calculate_category_total(
        values_by_name, line_item_metadata, "income", category_metadata
    )
    print(f"✓ Function works with category_metadata: {result}")
    assert result == 1500.0

    # This should fail without category_metadata
    try:
        _calculate_category_total(values_by_name, line_item_metadata, "income")
        print("✗ Function should have failed without category_metadata")
    except TypeError as e:
        print(f"✓ Function correctly requires category_metadata: {e}")

    # Test with invalid category
    try:
        _calculate_category_total(
            values_by_name, line_item_metadata, "nonexistent", category_metadata
        )
        print("✗ Function should have failed with invalid category")
    except KeyError as e:
        print(f"✓ Function correctly validates category exists: {e}")


if __name__ == "__main__":
    test_category_metadata_required()
    print("\nAll tests passed! ✓")
