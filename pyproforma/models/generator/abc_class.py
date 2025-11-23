from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class Generator(ABC):
    """
    Abstract base class for components that define and generate multiple fields.

    Generators create fields that can be accessed by line items using the
    "generator_name: field_name" formula syntax. The fields are stored in the
    value matrix with "generator_name.field" keys.

    Subclasses must implement the defined_names property (returning field names
    without the generator name prefix) and get_values method.

    Examples of subclasses might be:
    - Debt (generating principal, interest, bond_proceeds, and debt_outstanding fields)
    - ShortTermDebt (generating debt_outstanding, draw, principal, and interest fields)
    - DepreciationSchedule (generating depreciation fields for multiple assets)
    """

    # Registry to store generator subclasses by type
    _registry: Dict[str, Type["Generator"]] = {}

    @classmethod
    def register(cls, generator_type: str):
        """Decorator to register a generator subclass with a specific type."""

        def decorator(subclass: Type["Generator"]):
            cls._registry[generator_type] = subclass
            return subclass

        return decorator

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Generator":
        """
        Create a generator instance from a configuration dictionary.

        Args:
            config (Dict[str, Any]): Configuration dictionary with 'type' key

        Returns:
            Generator: Instance of the appropriate generator subclass

        Raises:
            ValueError: If the generator type is not registered
        """
        generator_type = config.get("type")
        if not generator_type:
            raise ValueError("Configuration must include a 'type' field")

        if generator_type not in cls._registry:
            raise ValueError(
                f"Unknown generator type: {generator_type}. "
                f"Available types: {list(cls._registry.keys())}"
            )

        generator_class = cls._registry[generator_type]
        return generator_class.from_config(config)

    @classmethod
    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> "Generator":
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
        Returns a list of all field names defined by this generator.

        Field names should not include the generator name prefix. The framework
        will automatically prepend the generator name when storing values in
        the value matrix (e.g., "field" becomes "generator_name.field").

        Returns:
            List[str]: The field names this generator can generate values for.  # noqa: E501
        """  # noqa: E501
        pass

    @abstractmethod
    def get_values(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> Dict[str, Optional[float]]:
        """
        Get all field values for this generator for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used to prevent circular references and for formula calculations.  # noqa: E501
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.

        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined fields in this  # noqa: E501
                                        generator for the specified year, with field names as keys.  # noqa: E501
                                        Keys should match the field names returned by defined_names.  # noqa: E501

        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.  # noqa: E501
        """  # noqa: E501
        pass
