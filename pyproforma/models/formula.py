import re
import numexpr as ne
from typing import Dict

    
def calculate_formula(formula: str, value_matrix: Dict[int, Dict[str, float]], year: int) -> float:
    """
    Calculate the result of a formula string using variable values from a matrix.
    
    This function evaluates mathematical formulas that can reference variables by name
    and support time-based offsets (e.g., revenue[-1] for previous year's revenue).
    
    Args:
        formula (str): The formula string to evaluate (e.g., "revenue - expenses" or "revenue[-1] * 1.1")
        value_matrix (Dict[int, Dict[str, float]]): Matrix of values organized by year and variable name
        year (int): The current year for which to evaluate the formula
        
    Returns:
        float: The calculated result of the formula
        
    Raises:
        ValueError: If a referenced variable or year is not found in the value matrix
        
    Examples:
        >>> matrix = {2023: {'revenue': 1000, 'expenses': 800}, 2024: {'revenue': 1100, 'expenses': 850}}
        >>> calculate_formula("revenue - expenses", matrix, 2024)
        250.0
        >>> calculate_formula("revenue[-1] * 1.1", matrix, 2024)  # Previous year's revenue * 1.1
        1100.0
    """
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
            raise ValueError(f"Variable '{var}' has None value for year {target_year}. Cannot use None values in formulas.")
        return str(value)

    # Replace all occurrences like revenue[-1], cost[-2], etc.
    formula = re.sub(r'([\w.]+)\[(-?\d+)\]', replace_offset, formula)

    # Replace variables like 'revenue' with their value for the current year
    for var in re.findall(r'\b[\w.]+\b', formula):
        if var.isidentifier() and var not in value_matrix.get(year, {}):
            raise ValueError(f"Variable '{var}' not found for year {year}.")
        if var in value_matrix.get(year, {}):
            value = value_matrix[year][var]
            if value is None:
                raise ValueError(f"Variable '{var}' has None value for year {year}. Cannot use None values in formulas.")
            formula = formula.replace(var, str(value))

    # Evaluate the formula using numexpr
    return float(ne.evaluate(formula))

