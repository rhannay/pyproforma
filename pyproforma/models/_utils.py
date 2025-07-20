import re
from typing import Dict, Any

def check_name(name) -> bool:
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        return False
    return True


def check_interim_values_by_year(values_by_year: Dict[int, Dict[str, Any]]) -> tuple[bool, str | None]:
    """
    Validates a dictionary of interim values organized by year.
    
    Requirements:
    - Keys must be years (integers) and in ascending order
    - Values must be dictionaries mapping variable names to values
    - All years except the last must contain the same set of variables
    - The last year may contain a subset of the variables from previous years
    
    Args:
        values_by_year (Dict[int, Dict[str, Any]]): Dictionary mapping years to value dictionaries
        
    Returns:
        tuple[bool, str | None]: A tuple containing:
            - bool: True if the structure is valid, False otherwise
            - str | None: Error message if invalid, None if valid
    """
    if not values_by_year:
        return True, None  # Empty dict is valid
        
    # Check if keys are years and in ascending order
    years = list(values_by_year.keys())
    if not all(isinstance(year, int) for year in years):
        return False, "All keys must be integers representing years"
        
    sorted_years = sorted(years)
    if sorted_years != years:
        return False, "Years must be in ascending order"
        
    # Check if all values are dictionaries
    non_dict_years = [year for year in years if not isinstance(values_by_year[year], dict)]
    if non_dict_years:
        return False, f"Values for years {non_dict_years} must be dictionaries"
        
    # If there's only one year, nothing more to check
    if len(years) <= 1:
        return True, None
        
    # Get the set of variable names from the first year
    reference_year = years[0]
    reference_names = set(values_by_year[reference_year].keys())
    
    # Check that all years except the last one have the same variable names
    for year in years[1:-1]:
        current_names = set(values_by_year[year].keys())
        if current_names != reference_names:
            missing = reference_names - current_names
            extra = current_names - reference_names
            error_msg = f"Year {year} has inconsistent variable names with the first year ({reference_year})"
            if missing:
                error_msg += f", missing: {', '.join(missing)}"
            if extra:
                error_msg += f", extra: {', '.join(extra)}"
            return False, error_msg
            
    # Check that the last year only has keys that are within the reference set
    last_year = years[-1]
    last_year_names = set(values_by_year[last_year].keys())
    extra_keys = last_year_names - reference_names
    if extra_keys:
        return False, f"Last year ({last_year}) contains extra variables not present in previous years: {', '.join(extra_keys)}"
        
    return True, None


