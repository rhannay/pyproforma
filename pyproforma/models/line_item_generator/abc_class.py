from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class LineItemGenerator(ABC):
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
    def get_values(self, interim_values_by_year: Dict[int, Dict[str, Any]],
                  year: int) -> Dict[str, Optional[float]]:
        """
        Get all values for this line item generator for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.
            
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this
                                        component for the specified year, with line item names as keys.
                             
        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.
        """
        pass
