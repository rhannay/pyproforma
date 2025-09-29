#!/usr/bin/env python3
"""
Quick test for improved pandas Series validation using _is_values_dict
"""

import os
import sys

# Add the current directory to the path so we can import pyproforma
sys.path.insert(0, os.getcwd())

import pandas as pd

from pyproforma import Model

print("Testing improved pandas Series validation using _is_values_dict")

# Create a model with some years
model = Model(years=[2023, 2024, 2025])

# Test 1: Valid pandas Series (should work)
print("\nTest 1: Valid pandas Series")
try:
    series_valid = pd.Series({2023: 100, 2024: 110, 2025: 121})
    model["revenue"] = series_valid
    print("✅ Valid Series accepted")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

# Test 2: Invalid index types (should fail)
print("\nTest 2: Invalid index types")
try:
    series_float_index = pd.Series({2023.0: 100, 2024.0: 110})
    model["invalid_float"] = series_float_index
    print("❌ Should have failed!")
except TypeError as e:
    print(f"✅ Correctly rejected float index: {e}")

try:
    series_string_index = pd.Series({"2023": 100, "2024": 110})
    model["invalid_string"] = series_string_index
    print("❌ Should have failed!")
except TypeError as e:
    print(f"✅ Correctly rejected string index: {e}")

# Test 3: Invalid value types (should fail)
print("\nTest 3: Invalid value types")
try:
    series_string_values = pd.Series({2023: "invalid", 2024: 110})
    model["invalid_values"] = series_string_values
    print("❌ Should have failed!")
except TypeError as e:
    print(f"✅ Correctly rejected non-numeric values: {e}")

print("\nImproved validation using _is_values_dict works perfectly! ✅")
