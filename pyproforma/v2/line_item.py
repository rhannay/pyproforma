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
    """

    def __init__(self, label: str | None = None):
        """
        Initialize a LineItem.

        Args:
            label (str, optional): Human-readable label. Defaults to None.
        """
        self.label = label

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
