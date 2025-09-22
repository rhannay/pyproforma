from dataclasses import dataclass
from typing import Dict, Literal, Union

from ._utils import validate_name


@dataclass
class Constraint:
    """
    Represents a constraint in a financial model that compares a line item value to a target value.

    A Constraint defines a relationship between a line item and a target value using comparison
    operators like equal to, less than, greater than, etc. It's used to enforce business rules
    and validation in financial models.

    Args:
        name (str): Unique identifier for the constraint. Must contain only letters,
            numbers, underscores, or hyphens (no spaces or special characters).
        line_item_name (str): Name of the line item this constraint applies to.
        target (Union[float, Dict[int, float]]): The target value for the constraint comparison.
            Can be a single float value or a dictionary mapping years to target values.
        operator (Literal['eq', 'lt', 'le', 'gt', 'ge', 'ne']): The comparison operator. Must be one of: 'eq' (equal to),
            'lt' (less than), 'le' (less than or equal), 'gt' (greater than),
            'ge' (greater than or equal), 'ne' (not equal).
        tolerance (float, optional): The tolerance for approximate comparisons. Defaults to 0.0.
            For 'eq': constraint passes if |actual - target| <= tolerance
            For 'lt': constraint passes if actual < target - tolerance
            For 'le': constraint passes if actual <= target + tolerance
            For 'gt': constraint passes if actual > target + tolerance
            For 'ge': constraint passes if actual >= target - tolerance
            For 'ne': constraint passes if |actual - target| > tolerance
        label (str, optional): Display label for the constraint. If None, the name will be used as the label.

    Raises:
        ValueError: If name contains invalid characters, operator is not valid, or tolerance is negative.

    Examples:
        >>> # Create a constraint that revenue must be greater than 50000
        >>> revenue_constraint = Constraint(
        ...     name="min_revenue",
        ...     line_item_name="revenue",
        ...     target=50000.0,
        ...     operator="gt"
        ... )

        >>> # Create a constraint with tolerance for approximate equality
        >>> balance_constraint = Constraint(
        ...     name="balance_check",
        ...     line_item_name="balance",
        ...     target=100000.0,
        ...     operator="eq",
        ...     tolerance=0.01  # Within 1 cent
        ... )

        >>> # Create a constraint that expenses must be less than budget with buffer
        >>> expense_constraint = Constraint(
        ...     name="expense_budget",
        ...     line_item_name="expenses",
        ...     target=100000.0,
        ...     operator="lt",
        ...     tolerance=1000.0  # Must be at least $1000 under budget
        ... )
    """  # noqa: E501

    VALID_OPERATORS = {"eq", "lt", "le", "gt", "ge", "ne"}

    name: str
    line_item_name: str
    target: Union[float, Dict[int, float]]
    operator: Literal["eq", "lt", "le", "gt", "ge", "ne"]
    tolerance: float = 0.0
    label: str = None

    def __post_init__(self):
        """Validate the constraint parameters after initialization."""
        validate_name(self.name)
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(
                f"Operator must be one of: {', '.join(self.VALID_OPERATORS)}"
            )
        if self.tolerance < 0:
            raise ValueError("Tolerance must be non-negative")

        if isinstance(self.target, dict):
            try:
                self.target = {int(k): float(v) for k, v in self.target.items()}
            except Exception:
                raise ValueError(
                    "All values in target dict must be convertible to float"
                    " and keys to int."
                )
            if not self.target:
                raise ValueError("Target dict must not be empty.")
        else:
            try:
                self.target = float(self.target)
            except Exception:
                raise ValueError(
                    "Target must be convertible to float or a dict of year:float."
                )

    def to_dict(self) -> dict:
        """Convert Constraint to dictionary representation."""
        return {
            "name": self.name,
            "label": self.label,
            "line_item_name": self.line_item_name,
            "target": self.target,
            "operator": self.operator,
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, constraint_dict: dict) -> "Constraint":
        """Create Constraint from dictionary."""
        return cls(
            name=constraint_dict["name"],
            line_item_name=constraint_dict["line_item_name"],
            target=constraint_dict["target"],
            operator=constraint_dict["operator"],
            tolerance=constraint_dict.get("tolerance", 0.0),
            label=constraint_dict.get("label", None),
        )
