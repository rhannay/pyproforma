"""Formula evaluation and validation functions."""

import ast
import operator
import re
from typing import Dict, List, Union


def validate_formula(formula: str, name: str, valid_names: List[str]) -> None:
    """
    Validate that all variable names in a formula are included in the provided list of valid names.

    This function checks both regular variable references (e.g., 'revenue') and time-offset
    references (e.g., 'revenue[-1]') to ensure all variables exist in the model. It also
    validates that the line item name itself is in the valid names, checks for circular
    references (i.e., a formula referencing its own name without a time offset or with [0]),
    and ensures no positive time offsets are used (future references are not allowed).

    Special formulas like "category_total:category_name" are recognized and skipped from
    regular validation.

    Args:
        formula (str): The formula string to validate (e.g., "revenue - expenses" or "revenue[-1] * 1.1")
        name (str): The name of the line item this formula belongs to
        valid_names (List[str]): List of valid variable names available in the model

    Raises:
        ValueError: If the line item name is not in valid_names, if any variable referenced
                   in the formula is not found in the valid_names list, if the formula
                   contains a circular reference to its own name without a time offset or
                   with [0] offset, or if the formula contains positive time offsets (future references)

    Examples:
        >>> validate_formula("revenue - expenses", "profit", ["revenue", "expenses", "profit"])
        # No error - all variables found and no circular reference
        >>> validate_formula("revenue[-1] * 1.1", "revenue", ["revenue", "expenses"])
        # No error - negative time offset reference is allowed
        >>> validate_formula("profit + expenses", "profit", ["profit", "expenses"])
        # Raises ValueError - circular reference without time offset
        >>> validate_formula("revenue[1] + expenses", "projection", ["revenue", "expenses", "projection"])
        # Raises ValueError - positive time offset not allowed
        >>> validate_formula("category_total:revenue", "total_rev", ["total_rev"])
        # No error - category_total formulas are skipped
    """  # noqa: E501
    # Check that the line item name is in valid_names
    if name not in valid_names:
        raise ValueError(f"Line item name '{name}' is not found in valid names")

    # Strip whitespace from the formula
    formula = formula.strip()

    # Check if this is a category_total formula - if so, skip regular validation
    # Pattern: "category_total:" followed by optional space and category name
    category_total_pattern = r'^category_total:\s*\w+$'
    if re.match(category_total_pattern, formula):
        # This is a category_total formula, skip regular validation
        # The category name will be validated during calculation
        return

    # Extract variables from time-offset patterns like revenue[-1], cost[-2], etc.
    offset_vars = re.findall(r"([\w.]+)\[(-?\d+)\]", formula)
    offset_var_names = [var for var, offset in offset_vars]

    # Extract all potential variable names from the formula
    all_potential_vars = re.findall(r"\b[\w.]+\b", formula)

    # Filter to only include valid identifiers that aren't Python keywords or built-ins
    # and exclude numeric literals. For dotted names, check if they're valid variable names  # noqa: E501
    import keyword

    formula_vars = set()
    for var in all_potential_vars:
        # Check if it's a simple identifier or a dotted name
        is_valid_var = False
        if var.isidentifier():
            # Simple identifier
            is_valid_var = (
                not keyword.iskeyword(var)
                and var not in ["True", "False", "None"]
                and not var.replace("_", "").isdigit()
            )
        elif "." in var:
            # Dotted name - check each part is a valid identifier
            parts = var.split(".")
            is_valid_var = all(
                part.isidentifier()
                and not keyword.iskeyword(part)
                and part not in ["True", "False", "None"]
                and not part.replace("_", "").isdigit()
                for part in parts
            )

        if is_valid_var:
            formula_vars.add(var)

    # Add variables from offset patterns
    formula_vars.update(offset_var_names)

    # Check for circular reference (formula referencing its own name without time
    # offset or with [0] offset)
    if name in formula_vars:
        # Check if the name appears without a time offset
        # We need to check if 'name' appears in the formula but not as
        # part of name[offset]
        pattern = rf"\b{re.escape(name)}\b(?!\[)"
        if re.search(pattern, formula):
            raise ValueError(
                (
                    f"Circular reference detected: formula for '{name}' "
                    "references itself without a time offset"
                )
            )

    # Check for circular reference with [0] time offset (which is equivalent to no offset)  # noqa: E501
    pattern_with_zero_offset = rf"\b{re.escape(name)}\[0\]"
    if re.search(pattern_with_zero_offset, formula):
        raise ValueError(
            f"Circular reference detected: formula for '{name}' references itself with [0] time offset, which is equivalent to no time offset"  # noqa: E501
        )

    # Check for positive time offsets (future references) which are not allowed
    positive_offset_vars = [
        (var, int(offset)) for var, offset in offset_vars if int(offset) > 0
    ]
    if positive_offset_vars:
        error_details = []
        for var, offset in positive_offset_vars:
            error_details.append(f"{var}[{offset}]")
        raise ValueError(
            f"Future time references are not allowed: {', '.join(error_details)}"
        )

    # Check if all formula variables are in the provided valid_names list
    missing_vars = formula_vars - set(valid_names)

    if missing_vars:
        missing_list = sorted(missing_vars)
        raise ValueError(
            f"Formula contains undefined line item names: {', '.join(missing_list)}"
        )


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
