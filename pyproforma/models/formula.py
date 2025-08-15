import re
import numexpr as ne
from typing import Dict, List

    
def validate_formula(formula: str, variables: List[str]) -> None:
    """
    Validate that all variable names in a formula are included in the provided list of variables.
    
    This function checks both regular variable references (e.g., 'revenue') and time-offset 
    references (e.g., 'revenue[-1]') to ensure all variables exist in the model.
    
    Args:
        formula (str): The formula string to validate (e.g., "revenue - expenses" or "revenue[-1] * 1.1")
        variables (List[str]): List of valid variable names available in the model
        
    Raises:
        ValueError: If any variable referenced in the formula is not found in the variables list
        
    Examples:
        >>> validate_formula("revenue - expenses", ["revenue", "expenses", "profit"])
        # No error - all variables found
        >>> validate_formula("revenue[-1] * growth_rate", ["revenue", "expenses"])
        # Raises ValueError - 'growth_rate' not found
    """
    # Strip whitespace from the formula
    formula = formula.strip()
    
    # Extract variables from time-offset patterns like revenue[-1], cost[-2], etc.
    offset_vars = re.findall(r'([\w.]+)\[(-?\d+)\]', formula)
    offset_var_names = [var for var, offset in offset_vars]
    
    # Extract all potential variable names from the formula
    all_potential_vars = re.findall(r'\b[\w.]+\b', formula)
    
    # Filter to only include valid identifiers that aren't Python keywords or built-ins
    # and exclude numeric literals
    import keyword
    formula_vars = set()
    for var in all_potential_vars:
        if (var.isidentifier() and 
            not keyword.iskeyword(var) and 
            var not in ['True', 'False', 'None'] and
            not var.replace('.', '').replace('_', '').isdigit()):
            formula_vars.add(var)
    
    # Add variables from offset patterns
    formula_vars.update(offset_var_names)
    
    # Check if all formula variables are in the provided variables list
    missing_vars = formula_vars - set(variables)
    
    if missing_vars:
        missing_list = sorted(missing_vars)
        raise ValueError(f"Formula contains undefined line item names: {', '.join(missing_list)}")


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

