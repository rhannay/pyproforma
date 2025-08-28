from ..constants import RESERVED_CATEGORY_NAMES
from ._utils import check_name


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

    def __init__(
        self,
        name: str,
        label: str = None,
        include_total: bool = True,
        total_label: str = None,
    ):
        if not check_name(name):
            raise ValueError(
                "Category name must only contain letters, numbers, underscores, "
                "or hyphens (no spaces or special characters)."
            )

        if name in RESERVED_CATEGORY_NAMES:
            raise ValueError(
                f"Category name '{name}' is reserved and cannot be used. Reserved names are: "  # noqa: E501
                f"{', '.join(RESERVED_CATEGORY_NAMES)}"
            )

        self.name = name
        self.label = label if label is not None else name
        self.include_total = include_total

        if include_total:
            self.total_label = (
                total_label if total_label is not None else f"Total {self.label}"
            )
            self.total_name = f"total_{self.name}"
        else:
            self.total_label = None
            self.total_name = None

    def __str__(self):
        return (
            f"Category("
            f"name='{self.name}', "
            f"label='{self.label}', "
            f"total_label='{self.total_label}', "
            f"total_name='{self.total_name}', "
            f"include_total={self.include_total}"
            f")"
        )

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        """Convert Category to dictionary representation."""
        return {
            "name": self.name,
            "label": self.label,
            "total_label": self.total_label,
            "include_total": self.include_total,
        }

    @classmethod
    def from_dict(cls, category_dict: dict) -> "Category":
        """Create Category from dictionary."""
        return cls(
            name=category_dict["name"],
            label=category_dict.get("label"),
            total_label=category_dict.get("total_label"),
            include_total=category_dict.get("include_total", True),
        )
