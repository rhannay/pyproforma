#!/usr/bin/env python3
"""
Test script to verify the Tables.line_items() fix for multiple included_cols
with include_totals=True.
"""

from pyproforma import Category, LineItem, Model


def main():
    """Test the fix for Tables.line_items with multiple included_cols and totals."""
    print("Testing Tables.line_items() fix...")

    # Create test model
    line_items = [
        LineItem(
            name="item_a",
            label="Item A",
            category="cat1",
            values={2023: 100, 2024: 110},
        ),
        LineItem(
            name="item_b",
            label="Item B",
            category="cat1",
            values={2023: 200, 2024: 220},
        ),
        LineItem(
            name="item_c",
            label="Item C",
            category="cat2",
            values={2023: 300, 2024: 330},
        ),
    ]
    categories = [
        Category(name="cat1", label="Category 1"),
        Category(name="cat2", label="Category 2"),
    ]
    model = Model(line_items=line_items, years=[2023, 2024], categories=categories)

    # Test cases that previously failed
    test_cases = [
        {
            "name": "Two columns with totals",
            "kwargs": {"included_cols": ["name", "label"], "include_totals": True},
        },
        {
            "name": "Three columns with totals",
            "kwargs": {
                "included_cols": ["name", "label", "category"],
                "include_totals": True,
            },
        },
        {
            "name": "Two columns with totals and grouping",
            "kwargs": {
                "included_cols": ["name", "category"],
                "group_by_category": True,
                "include_totals": True,
            },
        },
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            table = model.tables.line_items(**test_case["kwargs"])
            print(f"  ✅ Success: {len(table.rows)} rows, {len(table.columns)} columns")

            # Verify all rows have consistent cell count
            expected_cells = len(table.columns)
            for i, row in enumerate(table.rows):
                actual_cells = len(row.cells)
                if actual_cells != expected_cells:
                    print(
                        f"  ❌ Row {i} has {actual_cells} cells, expected {expected_cells}"
                    )
                    return False
            print(f"  ✅ All rows have {expected_cells} cells as expected")

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False

    print("\n🎉 All tests passed! The fix is working correctly.")
    return True


if __name__ == "__main__":
    main()
