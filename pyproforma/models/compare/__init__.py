"""
Compare package for model comparison functionality.

This package provides classes for comparing financial models:
- TwoModelCompare: Optimized comparison between exactly two models
- MultiModelCompare: Comparison across multiple (3+) models
- compare_models(): Function that returns the appropriate comparison class
"""

from .multi_model_compare import MultiModelCompare, compare_models
from .two_model_compare import TwoModelCompare

__all__ = ["TwoModelCompare", "MultiModelCompare", "compare_models"]
