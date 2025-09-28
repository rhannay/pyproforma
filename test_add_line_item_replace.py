#!/usr/bin/env python3
"""
Quick test script for the new replace parameter in add_line_item method.
"""

from pyproforma.models.line_item import LineItem
from pyproforma.models.model import Model


def test_add_line_item_replace():
    """Test the replace parameter functionality."""
    model = Model(years=[2023, 2024])

    # Add initial item
    model.update.add_line_item(name="test_item", formula="100")
    assert model["test_item", 2023] == 100

    # Test replace=False (default) - should fail
    try:
        model.update.add_line_item(name="test_item", formula="200")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "already exists" in str(e)
        assert "replace=True" in str(e)

    # Test replace=True - should work
    model.update.add_line_item(name="test_item", formula="300", replace=True)
    assert model["test_item", 2023] == 300

    # Test replace with LineItem object
    line_item = LineItem(name="test_item", category="new_cat", formula="400")
    model.update.add_line_item(line_item=line_item, replace=True)
    assert model["test_item", 2023] == 400
    assert model._line_item_definition("test_item").category == "new_cat"

    # Test replace=True with non-existing item (should still work)
    model.update.add_line_item(name="new_item", formula="500", replace=True)
    assert model["new_item", 2023] == 500

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_add_line_item_replace()
