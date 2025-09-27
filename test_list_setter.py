#!/usr/bin/env python3
"""
Test script for the updated Model setter functionality with list support.
"""

from pyproforma import Model

# Test 1: Basic list functionality
print("Test 1: Setting line item with list of values")
model = Model(years=[2023, 2024, 2025])
model["revenue_growth"] = [1000, 1100, 1210]
print(f"Years: {model.years}")
print(f"Values: {[model['revenue_growth', year] for year in model.years]}")
print(f"Expected: [1000.0, 1100.0, 1210.0]")
print()

# Test 2: List with mixed int/float values
print("Test 2: Mixed int/float list")
model["mixed_values"] = [100, 110.5, 121]
print(f"Values: {[model['mixed_values', year] for year in model.years]}")
print(f"Expected: [100.0, 110.5, 121.0]")
print()

# Test 3: Error case - wrong list length
print("Test 3: Error with wrong list length")
try:
    model["wrong_length"] = [100, 200]  # Only 2 values for 3 years
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {e}")
print()

# Test 4: Error case - non-numeric values in list
print("Test 4: Error with non-numeric values in list")
try:
    model["invalid_list"] = [100, "not_a_number", 300]
except TypeError as e:
    print(f"✓ Correctly raised TypeError: {e}")
print()

# Test 5: Error case - empty model
print("Test 5: Error with empty model")
empty_model = Model()
try:
    empty_model["test"] = [100, 200, 300]
except ValueError as e:
    print(f"✓ Correctly raised ValueError: {e}")
print()

# Test 6: Updating existing line item with list
print("Test 6: Updating existing line item with list")
model["existing_item"] = 500  # Create with constant value
print(f"Initial values: {[model['existing_item', year] for year in model.years]}")
model["existing_item"] = [600, 700, 800]  # Update with list
print(f"Updated values: {[model['existing_item', year] for year in model.years]}")
print(f"Expected: [600.0, 700.0, 800.0]")
print()

# Test 7: Single year model
print("Test 7: Single year model with list")
single_year_model = Model(years=[2023])
single_year_model["single_value"] = [42]
print(f"Single year value: {single_year_model['single_value', 2023]}")
print(f"Expected: 42.0")
print()

# Test 8: Verify backward compatibility with constants still works
print("Test 8: Backward compatibility with constants")
model["constant_item"] = 999
print(f"Constant values: {[model['constant_item', year] for year in model.years]}")
print(f"Expected: [999.0, 999.0, 999.0]")
print()

print("All tests completed!")
