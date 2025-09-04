#!/usr/bin/env python3
"""Test script to verify empty model initialization works."""

import sys
import os

# Add the pyproforma directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyproforma'))

from pyproforma.models.model.model import Model

def test_empty_model():
    """Test creating an empty model."""
    try:
        # Test 1: Create completely empty model
        print("Testing Model()...")
        empty_model = Model()
        print("✓ Empty model created successfully!")
        print(f"  Default years: {empty_model.years}")
        print(f"  Line items count: {len(empty_model._line_item_definitions)}")
        print(f"  Categories count: {len(empty_model._category_definitions)}")
        
        # Test 2: Verify summary works
        print("\nTesting model.summary()...")
        summary = empty_model.summary()
        print("✓ Summary generated successfully!")
        print(f"  Years count: {summary['years_count']}")
        print(f"  Line items count: {summary['line_items_count']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating empty model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_empty_model()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
