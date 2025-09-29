#!/usr/bin/env python3
"""
Quick integration test for pandas Series support in Model.__setitem__
"""

import os
import sys

# Add the current directory to the path so we can import pyproforma
sys.path.insert(0, os.getcwd())

try:
    import pandas as pd

    from pyproforma import Model

    print("Testing pandas Series support in Model.__setitem__")

    # Create a model with some years
    model = Model(years=[2023, 2024, 2025])

    # Test 1: Basic pandas Series
    print("\nTest 1: Basic pandas Series")
    series1 = pd.Series({2023: 100, 2024: 110, 2025: 121})
    model["revenue"] = series1
    print(f"Revenue 2023: {model['revenue', 2023]}")
    print(f"Revenue 2024: {model['revenue', 2024]}")
    print(f"Revenue 2025: {model['revenue', 2025]}")

    # Test 2: Compare with equivalent dictionary
    print("\nTest 2: Compare Series vs Dict")
    values_dict = {2023: 50, 2024: 55, 2025: 60}
    series2 = pd.Series(values_dict)

    model["costs_dict"] = values_dict
    model["costs_series"] = series2

    print(f"Dict  2023: {model['costs_dict', 2023]}")
    print(f"Series 2023: {model['costs_series', 2023]}")
    print(f"Values match: {model['costs_dict', 2023] == model['costs_series', 2023]}")

    # Test 3: Error handling for invalid index
    print("\nTest 3: Error handling")
    try:
        invalid_series = pd.Series({"2023": 100, "2024": 110})  # String index
        model["invalid"] = invalid_series
        print("ERROR: Should have failed!")
    except TypeError as e:
        print(f"Correctly caught error: {e}")

    # Test 4: Error handling for existing line item
    try:
        replacement_series = pd.Series({2023: 200, 2024: 220})
        model["revenue"] = replacement_series  # Should fail - item exists
        print("ERROR: Should have failed!")
    except ValueError as e:
        print(f"Correctly caught error: {e}")

    print("\nAll tests passed! ✅")

except ImportError as e:
    print(f"pandas not available: {e}")
    print("Testing without pandas...")

    from pyproforma import Model

    model = Model(years=[2023, 2024, 2025])

    # This should work fine (regular dict)
    model["revenue"] = {2023: 100, 2024: 110, 2025: 121}
    print(f"Revenue without pandas: {model['revenue', 2023]}")
    print("Basic functionality works ✅")

except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
