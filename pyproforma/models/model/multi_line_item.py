from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class MultiLineItemABC(ABC):
    """
    Abstract base class for components that define and generate multiple line items.
    
    This class provides an interface for accessing multiple line items from a single
    component in a financial model. Subclasses must implement the defined_names property
    and get_value method.
    
    Examples of subclasses might be:
    - DepreciationSchedule (generating depreciation line items for multiple assets)
    - LoanAmortization (generating principal, interest, and balance line items)
    - RevenueBreakdown (generating revenue line items by product/service)
    """
    
    @property
    @abstractmethod
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.
        
        Returns:
            List[str]: The names of all line items this component can generate values for.
        """
        pass
    
    @abstractmethod
    def get_value(self, name: str, interim_values_by_year: Dict[int, Dict[str, Any]], 
                  year: int) -> Optional[float]:
        """
        Get the value for a specific line item in a specific year.
        
        Args:
            name (str): The name of the line item to retrieve.
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
            year (int): The year for which to get the value.
            
        Returns:
            Optional[float]: The calculated value for the specified line item and year,
                             or None if no value exists.
                             
        Raises:
            ValueError: If the requested name is not in defined_names.
            ValueError: If value already exists in interim_values_by_year to prevent circular references.
        """
        pass
