from typing import Literal, Union, Dict
from ._utils import check_name


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
    """
    
    VALID_OPERATORS = {'eq', 'lt', 'le', 'gt', 'ge', 'ne'}
    OPERATOR_SYMBOLS = {
        'eq': '==',
        'lt': '<',
        'le': '<=',
        'gt': '>',
        'ge': '>=',
        'ne': '!='
    }
    
    def __init__(
        self,
        name: str,
        line_item_name: str,
        target: Union[float, Dict[int, float]],
        operator: Literal['eq', 'lt', 'le', 'gt', 'ge', 'ne'],
        tolerance: float = 0.0,
        label: str = None
    ):
        if not check_name(name):
            raise ValueError("Constraint name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        if operator not in self.VALID_OPERATORS:
            raise ValueError(f"Operator must be one of: {', '.join(self.VALID_OPERATORS)}")
        if tolerance < 0:
            raise ValueError("Tolerance must be non-negative")
        self.name = name
        self._label = label
        self.line_item_name = line_item_name
        self.tolerance = tolerance
        if isinstance(target, dict):
            try:
                self.target = {int(k): float(v) for k, v in target.items()}
            except Exception:
                raise ValueError("All values in target dict must be convertible to float and keys to int.")
            if not self.target:
                raise ValueError("Target dict must not be empty.")
        else:
            try:
                self.target = float(target)
            except Exception:
                raise ValueError("Target must be convertible to float or a dict of year:float.")
        self.operator = operator

    @property
    def label(self) -> str:
        """
        Returns the label for the constraint. If no label was provided, returns the name.
        """
        return self._label if self._label is not None else self.name

    def get_target(self, year: int) -> Union[float, None]:
        """
        Returns the target value for the given year. If target is a float, returns it.
        If target is a dict, returns the value for the year or None if not present.
        """
        if isinstance(self.target, dict):
            return self.target.get(year, None)
        return self.target

    def evaluate(self, value_matrix: Dict[int, Dict[str, float]], year: int) -> bool:
        """
        Evaluate the constraint against a line item value from the value matrix for a specific year.
        
        Args:
            value_matrix: Dictionary mapping years to line_item_name:value dictionaries
            year: The specific year to evaluate the constraint for
            
        Returns:
            bool: True if the constraint is satisfied, False otherwise
            
        Raises:
            ValueError: If year or line item is not found in value_matrix, or no target available
        """
        if year not in value_matrix:
            raise ValueError(f"Year {year} not found in value_matrix")
        
        if self.line_item_name not in value_matrix[year]:
            raise ValueError(f"Line item '{self.line_item_name}' not found in value_matrix for year {year}")
        
        target_value = self.get_target(year)
        if target_value is None:
            raise ValueError(f"No target value available for year {year}")
        
        line_item_value = value_matrix[year][self.line_item_name]
        
        if self.operator == 'eq':
            return abs(line_item_value - target_value) <= self.tolerance
        elif self.operator == 'lt':
            return line_item_value < target_value - self.tolerance
        elif self.operator == 'le':
            return line_item_value <= target_value + self.tolerance
        elif self.operator == 'gt':
            return line_item_value > target_value + self.tolerance
        elif self.operator == 'ge':
            return line_item_value >= target_value - self.tolerance
        elif self.operator == 'ne':
            return abs(line_item_value - target_value) > self.tolerance
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    def variance(self, value_matrix: Dict[int, Dict[str, float]], year: int) -> float:
        """
        Calculate the variance (difference) between line item value and target for a specific year.
        
        Args:
            value_matrix: Dictionary mapping years to line_item_name:value dictionaries
            year: The specific year to calculate variance for
            
        Returns:
            float: The variance (actual - target) for the specified year
            
        Raises:
            ValueError: If year or line item is not found in value_matrix, or no target available
        """
        if year not in value_matrix:
            raise ValueError(f"Year {year} not found in value_matrix")
        
        if self.line_item_name not in value_matrix[year]:
            raise ValueError(f"Line item '{self.line_item_name}' not found in value_matrix for year {year}")
        
        target_value = self.get_target(year)
        if target_value is None:
            raise ValueError(f"No target value available for year {year}")
        
        actual_value = value_matrix[year][self.line_item_name]
        return actual_value - target_value

    def to_dict(self) -> dict:
        """Convert Constraint to dictionary representation."""
        return {
            'name': self.name,
            'label': self._label,
            'line_item_name': self.line_item_name,
            'target': self.target,
            'operator': self.operator,
            'tolerance': self.tolerance
        }

    @classmethod
    def from_dict(cls, constraint_dict: dict) -> 'Constraint':
        """Create Constraint from dictionary."""
        return cls(
            name=constraint_dict['name'],
            line_item_name=constraint_dict['line_item_name'],
            target=constraint_dict['target'],
            operator=constraint_dict['operator'],
            tolerance=constraint_dict.get('tolerance', 0.0),
            label=constraint_dict.get('label', None)
        )

    def __str__(self):
        operator_symbol = self.OPERATOR_SYMBOLS.get(self.operator, self.operator)
        if isinstance(self.target, dict):
            target_str = str(self.target)
        else:
            target_str = str(self.target)
        return (f"Constraint(name='{self.name}', "
                f"line_item_name='{self.line_item_name}', "
                f"condition='{self.line_item_name} {operator_symbol} {target_str}')")

    def __repr__(self):
        return self.__str__()