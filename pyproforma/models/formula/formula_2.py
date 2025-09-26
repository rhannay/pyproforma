import ast
import operator
from typing import Dict, Union


def _validate_indexed_value(
    node: ast.Subscript, value_matrix: Dict[int, Dict[str, float]], year: int
) -> float:
    """
    Handle variable lookup with indexing like var[-1].

    Args:
        node: AST Subscript node representing indexed variable access
        value_matrix: Matrix of values organized by year and variable name
        year: Current year for calculation

    Returns:
        float: The value from the matrix (0.0 if None)

    Raises:
        ValueError: If indexing is invalid or variable/year not found
    """
    # Extract variable name and index
    if not isinstance(node.value, ast.Name):
        raise ValueError("Only simple variable indexing is supported")
    var_name = node.value.id

    # Extract index value - handle different AST structures
    index = None
    if isinstance(node.slice, ast.Constant):
        # Direct constant: var[1]
        index = node.slice.value
    elif isinstance(node.slice, ast.UnaryOp) and isinstance(node.slice.op, ast.USub):
        # Negative constant: var[-1]
        if isinstance(node.slice.operand, ast.Constant):
            index = -node.slice.operand.value
        else:
            raise ValueError("Only constant integer indices are supported")
    else:
        raise ValueError("Only constant integer indices are supported")

    # Validate index
    if not isinstance(index, int):
        raise ValueError("Index must be an integer")
    if index >= 0:
        raise ValueError(f"Only negative indices are allowed, got {index}")

    # Calculate target year
    target_year = year + index  # index is negative, so this reduces the year

    # Look up the value in the target year
    if target_year not in value_matrix:
        raise ValueError(f"Year {target_year} not found in value matrix")
    if var_name not in value_matrix[target_year]:
        raise ValueError(f"Variable '{var_name}' not found for year {target_year}")
    value = value_matrix[target_year][var_name]
    if value is None:
        return 0.0
    return value


def evaluate(
    formula: str, value_matrix: Dict[int, Dict[str, float]], year: int
) -> Union[int, float]:
    """
    Safely evaluate a mathematical expression using AST with value matrix lookup.

    Args:
        formula (str): Mathematical expression to evaluate (e.g., "5 * 3 - 2 + 7 / 6")
        value_matrix (Dict[int, Dict[str, float]]): Matrix of values organized by year
            and variable name. None values are treated as 0.0.
        year (int): The current year for which to evaluate the formula

    Returns:
        Union[int, float]: The result of the mathematical expression

    Raises:
        ValueError: If the formula contains unsupported operations, syntax,
            or variable references
        SyntaxError: If the formula has invalid syntax

    Examples:
        >>> matrix = {2024: {'revenue': 1000.0, 'tax_rate': 0.1}}
        >>> evaluate("5 * 3 - 2 + 7 / 6", matrix, 2024)
        14.166666666666666
        >>> evaluate("revenue * tax_rate", matrix, 2024)
        100.0
    """
    # Define supported operations
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _evaluate_node(node):
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # Numbers and other constants
            return node.value
        elif isinstance(node, ast.Name):  # Variable names (no indexing)
            var_name = node.id
            # Look up the value in the current year
            if year not in value_matrix:
                raise ValueError(f"Year {year} not found in value matrix")
            if var_name not in value_matrix[year]:
                raise ValueError(f"Variable '{var_name}' not found for year {year}")
            value = value_matrix[year][var_name]
            if value is None:
                return 0.0
            return value
        elif isinstance(node, ast.Subscript):  # Variable with indexing like var[-1]
            return _validate_indexed_value(node, value_matrix, year)
        elif isinstance(node, ast.BinOp):  # Binary operations (+, -, *, /, etc.)
            left = _evaluate_node(node.left)
            right = _evaluate_node(node.right)
            op = operators.get(type(node.op))
            if op is None:
                raise ValueError(
                    f"Unsupported binary operation: {type(node.op).__name__}"
                )
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):  # Unary operations (+, -)
            operand = _evaluate_node(node.operand)
            op = operators.get(type(node.op))
            if op is None:
                raise ValueError(
                    f"Unsupported unary operation: {type(node.op).__name__}"
                )
            return op(operand)
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

    try:
        # Parse the formula into an AST (strip whitespace first)
        tree = ast.parse(formula.strip(), mode="eval")

        # Evaluate the AST
        result = _evaluate_node(tree.body)

        return result

    except SyntaxError as e:
        raise SyntaxError(f"Invalid formula syntax: {formula}") from e
    except ZeroDivisionError as e:
        raise ZeroDivisionError("Division by zero in formula") from e
    except Exception as e:
        raise ValueError(f"Error evaluating formula '{formula}': {str(e)}") from e
