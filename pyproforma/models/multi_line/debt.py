from typing import List, Dict, Optional, Any

from pyproforma.models.multi_line.multi_line_abc import MultiLineItemABC


class Debt(MultiLineItemABC):
    """
    Debt class for modeling debt related line items.
    Inherits from MultiLineItemABC.
    
    This class will handle debt related calculations including principal, interest payments, 
    and debt service schedule. Currently a placeholder implementation.
    """
    
    def __init__(self, 
                par_amounts: dict, 
                interest_rate: float, 
                term: int,
                existing_debt_service: list[dict] = None):
        """
        Initialize a Debt object with specified parameters.
        
        Args:
            par_amounts (dict): The principal amounts for each debt issue.
            interest_rate (float): The interest rate applied to the debt.
            term (int): The term of the debt in years.
            existing_debt_service (list[dict], optional): Pre-existing debt service schedule.
        """
        self.par_amounts = par_amounts
        self.interest_rate = interest_rate
        self.term = term
        self.existing_debt_service = existing_debt_service or []
    
    @property
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.
        
        Returns:
            List[str]: The names of all line items this component can generate values for.
        """
        # Placeholder implementation
        return []
    
    def get_values(self, interim_values_by_year: Dict[int, Dict[str, Any]],
                  year: int) -> Dict[str, Optional[float]]:
        """
        Get all values for this debt component for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
            year (int): The year for which to get the values.
            
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this
                                        component for the specified year, with line item names as keys.
                             
        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.
        """
        # Placeholder implementation
        result = {}
        
        # Check for circular references
        for name in self.defined_names:
            if (year in interim_values_by_year and 
                name in interim_values_by_year[year]):
                raise ValueError(f"Circular reference detected for '{name}' in year {year}.")
            
            # Will be implemented in future
            result[name] = None
            
        return result