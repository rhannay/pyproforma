from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Type

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
    
    # Registry to store line item generator subclasses by type
    _registry: Dict[str, Type['LineItemGenerator']] = {}
    
    @classmethod
    def register(cls, generator_type: str):
        """Decorator to register a line item generator subclass with a specific type."""
        def decorator(subclass: Type['LineItemGenerator']):
            cls._registry[generator_type] = subclass
            return subclass
        return decorator
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'LineItemGenerator':
        """
        Create a line item generator instance from a configuration dictionary.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary with 'type' key
            
        Returns:
            LineItemGenerator: Instance of the appropriate line item generator subclass
            
        Raises:
            ValueError: If the line item generator type is not registered
        """
        generator_type = config.get('type')
        if not generator_type:
            raise ValueError("Configuration must include a 'type' field")
        
        if generator_type not in cls._registry:
            raise ValueError(f"Unknown line item generator type: {generator_type}. "
                           f"Available types: {list(cls._registry.keys())}")
        
        generator_class = cls._registry[generator_type]
        return generator_class.from_config(config)
    
    @classmethod
    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'LineItemGenerator':
        """
        Create an instance from configuration dictionary.
        Each subclass must implement this method.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            
        Returns:
            LineItemGenerator: Instance of this line item generator
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the line item generator instance to a dictionary representation.
        Each subclass must implement this method.
        
        Returns:
            Dict[str, Any]: Dictionary representation including 'type' field
        """
        pass
    
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
