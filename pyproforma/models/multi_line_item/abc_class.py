from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class MultiLineItem(ABC):
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

    # Registry to store multi line item subclasses by type
    _registry: Dict[str, Type["MultiLineItem"]] = {}

    @classmethod
    def register(cls, generator_type: str):
        """Decorator to register a multi line item subclass with a specific type."""

        def decorator(subclass: Type["MultiLineItem"]):
            cls._registry[generator_type] = subclass
            return subclass

        return decorator

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "MultiLineItem":
        """
        Create a multi line item instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): Configuration dictionary with 'type' key

        Returns:
            MultiLineItem: Instance of the appropriate multi line item subclass

        Raises:
            ValueError: If the multi line item type is not registered
        """
        generator_type = config.get("type")
        if not generator_type:
            raise ValueError("Configuration must include a 'type' field")

        if generator_type not in cls._registry:
            raise ValueError(
                f"Unknown multi line item type: {generator_type}. "
                f"Available types: {list(cls._registry.keys())}"
            )

        generator_class = cls._registry[generator_type]
        return generator_class.from_config(config)

    @classmethod
    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> "MultiLineItem":
        """
        Create an instance from configuration dictionary.
        Each subclass must implement this method.

        Args:
            config (Dict[str, Any]): Configuration dictionary

        Returns:
            MultiLineItem: Instance of this multi line item
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the multi line item instance to a dictionary representation.
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
            List[str]: The names of all line items this component can generate values for.  # noqa: E501
        """  # noqa: E501
        pass

    @abstractmethod
    def get_values(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> Dict[str, Optional[float]]:
        """
        Get all values for this multi line item for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used to prevent circular references and for formula calculations.  # noqa: E501
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.

        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this  # noqa: E501
                                        component for the specified year, with line item names as keys.  # noqa: E501

        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.  # noqa: E501
        """  # noqa: E501
        pass
