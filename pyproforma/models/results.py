"""Results classes for analyzing financial model components."""

# Import all classes from the results submodule for backward compatibility
from .results.category_results import CategoryResults
from .results.constraint_results import ConstraintResults
from .results.line_item_results import LineItemResults

__all__ = ["LineItemResults", "CategoryResults", "ConstraintResults"]
