"""
Abstract base class for line items in ProformaModel.

LineItem provides the common interface that all line item types must implement.
This allows for type checking and ensures consistency across different line item types.
"""

from abc import ABC, abstractmethod
from typing import Any, Union

from pyproforma.table import Format, NumberFormatSpec, normalize_format


class LineItem(ABC):
    """
    Abstract base class for all line items in a ProformaModel.

    All concrete line item types (FixedLine, FormulaLine, etc.) inherit from this
    class and must implement the required methods.

    Attributes:
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
        value_format (str | NumberFormatSpec | dict, optional): Format specification
            for displaying values. Can be a string format name like 'percent',
            'currency', 'no_decimals', etc., a NumberFormatSpec instance for more
            control, or a dict. Defaults to 'no_decimals'.
    """

    def __init__(
        self,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        """
        Initialize a LineItem.

        Args:
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Tags enable flexible grouping and can be used to sum related items.
                Defaults to None (empty list).
            value_format (str | NumberFormatSpec | dict, optional): Format specification
                for displaying values. Can be a string format name like 'percent',
                'currency', 'no_decimals', etc., a NumberFormatSpec instance for more
                control, or a dict. Defaults to None (which uses 'no_decimals').
        """
        self.name: str | None = None  # Set by __set_name__ when assigned to class
        self.label = label
        self.tags = tags or []
        # Normalize value_format to NumberFormatSpec, defaulting to NO_DECIMALS
        self.value_format = (
            normalize_format(value_format)
            if value_format is not None
            else Format.NO_DECIMALS
        )

    def __set_name__(self, owner, name: str):
        """
        Store the attribute name when the descriptor is assigned to a class.

        This method is called automatically by Python when a descriptor is assigned
        to a class attribute. It allows line items to know their own names.

        Args:
            owner: The class that owns this descriptor.
            name (str): The attribute name.
        """
        self.name = name

    @abstractmethod
    def get_value(self, period: Any) -> Any:
        """
        Get the value for a specific period.

        Args:
            period (Any): The period to get the value for.

        Returns:
            Any: The value for the specified period.
        """
        pass
