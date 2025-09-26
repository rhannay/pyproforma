import ast
import operator
from typing import Any, Dict, Union


def evaluate(formula: str, variables: Dict[str, Any] = None) -> Union[int, float]:
    """
    Safely evaluate a mathematical expression using AST.

    Args:
        formula (str): Mathematical expression to evaluate (e.g., "5 * 3 - 2 + 7 / 6")
        variables (Dict[str, Any], optional): Dictionary of variables to use in formula

    Returns:
        Union[int, float]: The result of the mathematical expression

    Raises:
        ValueError: If the formula contains unsupported operations or syntax
        SyntaxError: If the formula has invalid syntax

    Examples:
        >>> evaluate("5 * 3 - 2 + 7 / 6")
        14.166666666666666
        >>> evaluate("2 + 3 * 4")
        14
        >>> evaluate("(10 + 5) / 3")
        5.0
        >>> evaluate("revenue * 0.1", {"revenue": 1000})
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
        elif isinstance(node, ast.Name):  # Variable names
            if variables is None:
                raise ValueError(f"Variable '{node.id}' used but no variables provided")
            if node.id not in variables:
                raise ValueError(f"Unknown variable: '{node.id}'")
            return variables[node.id]
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

