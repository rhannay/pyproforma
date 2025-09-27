#!/usr/bin/env python3
"""
Test script for the new Model setter functionality.
"""

from pyproforma import Model

# Test 1: Create a model with years and test the setter
print("Test 1: Basic setter functionality")
model = Model(years=[2023, 2024, 2025])
model["new_item"] = 99
print(f"Added 'new_item' with value 99")
print(f"Values: {[model['new_item', year] for year in model.years]}")
print()

# Test 2: Test with float value
print("Test 2: Float value")
model["profit_margin"] = 0.15
print(f"Added 'profit_margin' with value 0.15")
print(f"Values: {[model['profit_margin', year] for year in model.years]}")
print()

# Test 3: Test error when model has no years
print("Test 3: Error when no years defined")
empty_model = Model()
try:
    empty_model["test"] = 100
except ValueError as e:
    print(f"Expected error: {e}")
print()

# Test 4: Test error with invalid key type
print("Test 4: Error with invalid key type")
try:
    model[123] = 100
except TypeError as e:
    print(f"Expected error: {e}")
print()

# Test 5: Test error with invalid value type
print("Test 5: Error with invalid value type")
try:
    model["test"] = "not_a_number"
except TypeError as e:
    print(f"Expected error: {e}")
print()

# Test 6: Test that the line item is properly added to the model
print("Test 6: Verify line item is properly added")
print(f"Line item names: {model.line_item_names}")
print(f"'new_item' in names: {'new_item' in model.line_item_names}")
print(f"Can access via line_item method: {model.line_item('new_item').values}")
