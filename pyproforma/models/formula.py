import re
from typing import Dict, List

import numexpr as ne


def validate_formula(formula: str, name: str, valid_names: List[str]) -> None:
    """
    Validate that all variable names in a formula are included in the provided list of valid names.  # noqa: E501

    This function checks both regular variable references (e.g., 'revenue') and time-offset  # noqa: E501
    references (e.g., 'revenue[-1]') to ensure all variables exist in the model. It also
    validates that the line item name itself is in the valid names, checks for circular
    references (i.e., a formula referencing its own name without a time offset or with [0]),  # noqa: E501
    and ensures no positive time offsets are used (future references are not allowed).

    Args:
        formula (str): The formula string to validate (e.g., "revenue - expenses" or "revenue[-1] * 1.1")  # noqa: E501
        name (str): The name of the line item this formula belongs to
        valid_names (List[str]): List of valid variable names available in the model

    Raises:
        ValueError: If the line item name is not in valid_names, if any variable referenced  # noqa: E501
                   in the formula is not found in the valid_names list, if the formula
                   contains a circular reference to its own name without a time offset or  # noqa: E501
                   with [0] offset, or if the formula contains positive time offsets (future references)  # noqa: E501

    Examples:
        >>> validate_formula("revenue - expenses", "profit", ["revenue", "expenses", "profit"])  # noqa: E501
        # No error - all variables found and no circular reference
        >>> validate_formula("revenue[-1] * 1.1", "revenue", ["revenue", "expenses"])
        # No error - negative time offset reference is allowed
        >>> validate_formula("profit + expenses", "profit", ["profit", "expenses"])
        # Raises ValueError - circular reference without time offset
        >>> validate_formula("revenue[1] + expenses", "projection", ["revenue", "expenses", "projection"])  # noqa: E501
        # Raises ValueError - positive time offset not allowed
    """  # noqa: E501
    # Check that the line item name is in valid_names
    if name not in valid_names:
        raise ValueError(f"Line item name '{name}' is not found in valid names")

    # Strip whitespace from the formula
    formula = formula.strip()

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

    # Check for circular reference (formula referencing its own name without time offset or with [0] offset)  # noqa: E501
    if name in formula_vars:
        # Check if the name appears without a time offset
        # We need to check if 'name' appears in the formula but not as part of name[offset]  # noqa: E501
        pattern = rf"\b{re.escape(name)}\b(?!\[)"
        if re.search(pattern, formula):
            raise ValueError(
                f"Circular reference detected: formula for '{name}' references itself without a time offset"  # noqa: E501
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


def calculate_formula(
    formula: str, value_matrix: Dict[int, Dict[str, float]], year: int
) -> float:
    """
    Calculate the result of a formula string using variable values from a matrix.

    This function evaluates mathematical formulas that can reference variables by name
    and support time-based offsets (e.g., revenue[-1] for previous year's revenue).

    Args:
        formula (str): The formula string to evaluate (e.g., "revenue - expenses" or "revenue[-1] * 1.1")  # noqa: E501
        value_matrix (Dict[int, Dict[str, float]]): Matrix of values organized by year and variable name  # noqa: E501
        year (int): The current year for which to evaluate the formula

    Returns:
        float: The calculated result of the formula

    Raises:
        ValueError: If a referenced variable or year is not found in the value matrix

    Examples:
        >>> matrix = {2023: {'revenue': 1000, 'expenses': 800}, 2024: {'revenue': 1100, 'expenses': 850}}  # noqa: E501
        >>> calculate_formula("revenue - expenses", matrix, 2024)
        250.0
        >>> calculate_formula("revenue[-1] * 1.1", matrix, 2024)  # Previous year's revenue * 1.1  # noqa: E501
        1100.0
    """  # noqa: E501
    # strip whitespace from the formula
    formula = formula.strip()

    # Helper to replace var[-N] with the correct value
    def replace_offset(match):
        var = match.group(1)
        offset = int(match.group(2))
        target_year = year + offset
        # if year is missing, raise error
        if target_year not in value_matrix:
            raise ValueError(f"Year {target_year} not found in values.")
        if var not in value_matrix[target_year]:
            raise ValueError(f"Variable '{var}' not found for year {target_year}.")
        value = value_matrix[target_year][var]
        if value is None:
            raise ValueError(
                f"Variable '{var}' has None value for year {target_year}. Cannot use None values in formulas."  # noqa: E501
            )
        return str(value)

    # Replace all occurrences like revenue[-1], cost[-2], etc.
    formula = re.sub(r"([\w.]+)\[(-?\d+)\]", replace_offset, formula)

    # Replace variables like 'revenue' with their value for the current year
    for var in re.findall(r"\b[\w.]+\b", formula):
        if var.isidentifier() and var not in value_matrix.get(year, {}):
            raise ValueError(f"Variable '{var}' not found for year {year}.")
        if var in value_matrix.get(year, {}):
            value = value_matrix[year][var]
            if value is None:
                raise ValueError(
                    f"Variable '{var}' has None value for year {year}. Cannot use None values in formulas."  # noqa: E501
                )
            formula = formula.replace(var, str(value))

    # Evaluate the formula using numexpr
    return float(ne.evaluate(formula))
