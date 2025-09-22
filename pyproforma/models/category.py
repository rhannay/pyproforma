from dataclasses import dataclass

from ..constants import RESERVED_CATEGORY_NAMES
from ._utils import validate_name


@dataclass
class Category:
    """
    Represents a category for organizing line items in a financial model.

    A Category defines a grouping mechanism for line items and can optionally
    include a total calculation. It's used to organize and structure financial
    statements by grouping related line items together.

    Args:
        name (str): Unique identifier for the category. Must contain only letters,
            numbers, underscores, or hyphens (no spaces or special characters).
        label (str, optional): Human-readable display name for the category.
            Defaults to name if not provided.
        include_total (bool, optional): Whether to include a total calculation for
            this category. Defaults to True.
        total_label (str, optional): Label for the total line when include_total is True.
            Defaults to "Total {label}" if not provided.

    Attributes:
        name (str): The category's unique identifier.
        label (str): The display name for the category.
        include_total (bool): Whether this category includes a total.
        total_label (str or None): Label for the total line (None if include_total is False).
        total_name (str or None): Name for the total line item (None if include_total is False).

    Raises:
        ValueError: If name contains invalid characters (spaces or special characters).

    Examples:
        >>> # Create a category with default total
        >>> revenue_cat = Category(
        ...     name="revenue",
        ...     label="Revenue Sources"
        ... )
        >>> print(revenue_cat.total_label)  # "Total Revenue Sources"
        >>> print(revenue_cat.total_name)   # "total_revenue"

        >>> # Create a category without total
        >>> notes_cat = Category(
        ...     name="notes",
        ...     label="Notes and Assumptions",
        ...     include_total=False
        ... )
        >>> print(notes_cat.total_label)  # None

        >>> # Create a category with custom total label
        >>> expense_cat = Category(
        ...     name="operating_expenses",
        ...     label="Operating Expenses",
        ...     total_label="Total OpEx"
        ... )
    """  # noqa: E501

    name: str
    label: str = None
    include_total: bool = True
    total_label: str = None
    total_name: str = None

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
            "total_label": self.total_label,
            "total_name": self.total_name,
            "include_total": self.include_total,
        }

    @classmethod
    def from_dict(cls, category_dict: dict) -> "Category":
        """Create Category from dictionary."""
        return cls(
            name=category_dict["name"],
            label=category_dict.get("label"),
            total_label=category_dict.get("total_label"),
            total_name=category_dict.get("total_name"),
            include_total=category_dict.get("include_total", True),
        )
