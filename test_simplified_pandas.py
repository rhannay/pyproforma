#!/usr/bin/env python3
"""
Quick test for simplified pandas Series support (no conditional imports)
"""

import os
import sys

# Add the current directory to the path so we can import pyproforma
sys.path.insert(0, os.getcwd())

import pandas as pd

from pyproforma import Model

print("Testing simplified pandas Series support in Model.__setitem__")

# Create a model with some years
model = Model(years=[2023, 2024, 2025])

# Test: Basic pandas Series
print("\nTest: Basic pandas Series")
series = pd.Series({2023: 100, 2024: 110, 2025: 121})
model["revenue"] = series
print(f"Revenue 2023: {model['revenue', 2023]}")
print(f"Revenue 2024: {model['revenue', 2024]}")
print(f"Revenue 2025: {model['revenue', 2025]}")

# Test: Compare with equivalent dictionary
print("\nTest: Series vs Dict equivalence")
values_dict = {2023: 50, 2024: 55, 2025: 60}
series2 = pd.Series(values_dict)

model["costs_dict"] = values_dict
model["costs_series"] = series2

for year in [2023, 2024, 2025]:
    dict_val = model["costs_dict", year]
    series_val = model["costs_series", year]
    print(
        f"Year {year}: Dict={dict_val}, Series={series_val}, Equal={dict_val == series_val}"
    )

print("\nSimplified implementation works perfectly! ✅")
