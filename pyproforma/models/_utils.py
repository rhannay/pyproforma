import re
from typing import Dict, Any

def check_name(name) -> bool:
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        return False
    return True


def check_interim_values_by_year(values_by_year: Dict[int, Dict[str, Any]]) -> bool:
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
        bool: True if the structure is valid, False otherwise
    """
    if not values_by_year:
        return True  # Empty dict is valid
        
    # Check if keys are years and in ascending order
    years = list(values_by_year.keys())
    if not all(isinstance(year, int) for year in years):
        return False
        
    sorted_years = sorted(years)
    if sorted_years != years:
        return False
        
    # Check if all values are dictionaries
    if not all(isinstance(values_by_year[year], dict) for year in years):
        return False
        
    # If there's only one year, nothing more to check
    if len(years) <= 1:
        return True
        
    # Get the set of variable names from the first year
    reference_year = years[0]
    reference_names = set(values_by_year[reference_year].keys())
    
    # Check that all years except the last one have the same variable names
    for year in years[1:-1]:
        current_names = set(values_by_year[year].keys())
        if current_names != reference_names:
            return False
            
    # Check that the last year only has keys that are within the reference set
    last_year = years[-1]
    last_year_names = set(values_by_year[last_year].keys())
    if not last_year_names.issubset(reference_names):
        return False
        
    return True


