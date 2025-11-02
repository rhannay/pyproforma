"""
Examples Package for PyProforma

This package contains example models demonstrating various features of PyProforma.

Available examples:
- simple_model_1: Basic model with single revenue and expense items
- simple_model_2: Comprehensive model with multiple revenue/expense items and
  category totals
- model_with_debt: Model demonstrating debt financing with the Debt generator

Usage:
    from examples import simple_model_1, simple_model_2, model_with_debt

    # Use the models
    print(simple_model_1.to_dataframe())
    print(simple_model_2.to_dataframe())
    print(model_with_debt.to_dataframe())
"""

from .model_with_debt import model_with_debt
from .simple_model_1 import simple_model_1
from .simple_model_2 import simple_model_2

__all__ = ["simple_model_1", "simple_model_2", "model_with_debt"]
