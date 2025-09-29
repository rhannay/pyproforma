from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .line_item import LineItem

class Expression:
    def __init__(self, fn):
        self.fn = fn
    
    def _create_binary_operation(self, other: LineItem | float | "Expression", operation) -> "Expression":
        """Helper method to create binary operations with consistent logic."""
        from .line_item import LineItem
        
        if not isinstance(other, (LineItem, int, float, Expression)):
            raise ValueError(f'Unsupported type for operation: {type(other)}')

        other_expression = other
        if isinstance(other, (int, float)):
            other_expression = Expression(lambda year: other)
        elif isinstance(other, LineItem):
            other_expression = Expression(lambda year: other.get_value(year))
            
        def operation_expr(year):
            return operation(self.fn(year), other_expression.fn(year))
        return Expression(fn=operation_expr)

    def __add__(self, other: LineItem | float | "Expression") -> "Expression":
        return self._create_binary_operation(other, lambda a, b: a + b)

    def __sub__(self, other: LineItem | float | "Expression") -> "Expression":
        return self._create_binary_operation(other, lambda a, b: a - b)

    def __mul__(self, other: LineItem | float | "Expression") -> "Expression":
        return self._create_binary_operation(other, lambda a, b: a * b)

    def __true_div__(self, other: LineItem | float | "Expression") -> "Expression":
        return self._create_binary_operation(other, lambda a, b: a/b)