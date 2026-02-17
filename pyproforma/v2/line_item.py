"""
Abstract base class for line items in ProformaModel.

LineItem provides the common interface that all line item types must implement.
This allows for type checking and ensures consistency across different line item types.
"""

from abc import ABC, abstractmethod
from typing import Any


class LineItem(ABC):
    """
    Abstract base class for all line items in a ProformaModel.

    All concrete line item types (FixedLine, FormulaLine, etc.) inherit from this
    class and must implement the required methods.

    Attributes:
        label (str, optional): Human-readable label for display purposes.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def __init__(self, label: str | None = None, tags: list[str] | None = None):
        """
        Initialize a LineItem.

        Args:
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Tags enable flexible grouping and can be used to sum related items.
                Defaults to None (empty list).
        """
        self.name: str | None = None  # Set by __set_name__ when assigned to class
        self.label = label
        self.tags = tags or []

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
