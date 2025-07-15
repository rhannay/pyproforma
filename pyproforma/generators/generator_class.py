from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any


class Generator(ABC):
    """
    Abstract base class for financial model generators.
    
    Generators are objects that can create calculated values for financial models
    based on their specific logic (e.g., debt service schedules, depreciation schedules, etc.).
    
    All generators must implement:
    - defined_names: A property returning list of variable names this generator provides
    - get_values: A method returning calculated values for a given year
    """
    
    # Registry to store generator subclasses by type
    _registry: Dict[str, Type['Generator']] = {}
    
    @classmethod
    def register(cls, generator_type: str):
        """Decorator to register a generator subclass with a specific type."""
        def decorator(subclass: Type['Generator']):
            cls._registry[generator_type] = subclass
            return subclass
        return decorator
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'Generator':
        """
        Create a generator instance from a configuration dictionary.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary with 'type' key
            
        Returns:
            Generator: Instance of the appropriate generator subclass
            
        Raises:
            ValueError: If the generator type is not registered
        """
        generator_type = config.get('type')
        if not generator_type:
            raise ValueError("Configuration must include a 'type' field")
        
        if generator_type not in cls._registry:
            raise ValueError(f"Unknown generator type: {generator_type}. "
                           f"Available types: {list(cls._registry.keys())}")
        
        generator_class = cls._registry[generator_type]
        return generator_class.from_config(config)
    
    @classmethod
    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Generator':
        """
        Create an instance from configuration dictionary.
        Each subclass must implement this method.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            
        Returns:
            Generator: Instance of this generator
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the generator instance to a dictionary representation.
        Each subclass must implement this method.
        
        Returns:
            Dict[str, Any]: Dictionary representation including 'type' field
        """
        pass
    
    @property
    @abstractmethod
    def defined_names(self) -> List[str]:
        """
        Return a list of variable names that this generator provides.
        
        Returns:
            List[str]: List of variable names (e.g., ['debt.principal', 'debt.interest'])
        """
        pass
    
    @abstractmethod
    def get_values(self, year: int) -> Dict[str, float]:
        """
        Calculate and return values for all variables this generator provides for a given year.
        
        Args:
            year (int): The year for which to calculate values
            
        Returns:
            Dict[str, float]: Dictionary mapping variable names to their calculated values
        """
        pass