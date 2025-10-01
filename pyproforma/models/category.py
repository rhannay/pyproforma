from dataclasses import dataclass

from ..constants import RESERVED_CATEGORY_NAMES
from ._utils import validate_name


@dataclass
class Category:
    """
    Represents a category for organizing line items in a financial model.

    A Category defines a grouping mechanism for line items. It's used to organize
    and structure financial statements by grouping related line items together.

    Args:
        name (str): Unique identifier for the category. Must contain only letters,
            numbers, underscores, or hyphens (no spaces or special characters).
        label (str, optional): Human-readable display name for the category.
            Defaults to name if not provided.

    Attributes:
        name (str): The category's unique identifier.
        label (str): The display name for the category.

    Raises:
        ValueError: If name contains invalid characters (spaces or special characters).

    Examples:
        >>> # Create a simple category
        >>> revenue_cat = Category(
        ...     name="revenue",
        ...     label="Revenue Sources"
        ... )
        >>> print(revenue_cat.name)  # "revenue"
        >>> print(revenue_cat.label)  # "Revenue Sources"

        >>> # Create a category without label
        >>> notes_cat = Category(
        ...     name="notes"
        ... )
        >>> print(notes_cat.label)  # None
    """  # noqa: E501

    name: str
    label: str = None

    def __post_init__(self):
        validate_name(self.name)

        if self.name in RESERVED_CATEGORY_NAMES:
            raise ValueError(
                f"Category name '{self.name}' is reserved and cannot be used. Reserved names are: "  # noqa: E501
                f"{', '.join(RESERVED_CATEGORY_NAMES)}"
            )

    def to_dict(self) -> dict:
        """Convert Category to dictionary representation."""
        return {
            "name": self.name,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, category_dict: dict) -> "Category":
        """Create Category from dictionary."""
        return cls(
            name=category_dict["name"],
            label=category_dict.get("label"),
        )
