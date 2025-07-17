from dataclasses import dataclass, asdict
from typing import Optional, Union, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from pyproforma import Model

from .table_class import Row, Cell
from ..constants import ValueFormat


class BaseRow(ABC):
    """Base configuration for all row types."""
    
    @abstractmethod
    def generate_row(self, model: 'Model') -> Union[Row, list[Row]]:
        """Generate row(s) for this configuration."""
        pass
    
    def to_dict(self) -> dict:
        """Convert dataclass to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ItemRow(BaseRow):
    """Configuration for item row generation."""
    name: str
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row for a line item with its label and values across all years."""
        # Get label and value format from model if not specified
        label = model.line_item(self.name).label
        value_format = self.value_format or model.line_item(self.name).value_format
        
        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Add a cell for each year with the item's value for that year
        for year in model.years:
            value = model[self.name, year]
            cells.append(Cell(value=value, bold=self.bold, value_format=value_format))
        
        return Row(cells=cells)


@dataclass
class ItemsByCategoryRow(BaseRow):
    """Configuration for items by category row generation."""
    category: str
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> list[Row]:
        """Create rows for all line items in a specific category."""
        rows = []
        # Get all line items in the specified category
        for item in model.get_line_item_definitions_by_category(self.category):
            item_config = ItemRow(
                name=item.name,
                include_name=self.include_name,
                bold=self.bold,
                value_format=self.value_format
            )
            rows.append(item_config.generate_row(model))
        return rows


@dataclass
class PercentChangeRow(BaseRow):
    """Configuration for percent change row generation."""
    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing percent change of a line item from year to year."""
        # Get the original item's label if no custom label provided
        if self.label is None:
            original_label = model.line_item(self.name).label
            label = f"{original_label} % Change"
        else:
            label = self.label
        
        # Default to percentage format if not specified
        value_format = self.value_format or "percent_two_decimals"
        
        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Add cells for each year with percent change calculation
        for year in model.years:
            percent_change = model.percent_change(self.name, year)
            cells.append(Cell(value=percent_change, bold=self.bold, value_format=value_format))
        
        return Row(cells=cells)


@dataclass
class CumulativeChangeRow(BaseRow):
    """Configuration for cumulative change row generation."""
    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing cumulative change of a line item from the base year."""
        # Get the original item's label if no custom label provided
        if self.label is None:
            original_label = model.line_item(self.name).label
            label = f"{original_label} Cumulative Change"
        else:
            label = self.label
        
        # Default to same format as original item if not specified
        value_format = self.value_format or model.line_item(self.name).value_format
        
        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Get the base year value (first year)
        base_year = model.years[0]
        base_value = model[self.name, base_year]
        
        # Add cells for each year with cumulative change calculation
        for year in model.years:
            current_value = model[self.name, year]
            
            # Calculate cumulative change from base year (absolute change)
            if base_value is None or current_value is None:
                cumulative_change = None
            else:
                cumulative_change = current_value - base_value
            
            cells.append(Cell(value=cumulative_change, bold=self.bold, value_format=value_format))
        
        return Row(cells=cells)


@dataclass
class CumulativePercentChangeRow(BaseRow):
    """Configuration for cumulative percent change row generation."""
    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing cumulative percent change of a line item from the base year."""
        # Get the original item's label if no custom label provided
        if self.label is None:
            original_label = model.line_item(self.name).label
            label = f"{original_label} Cumulative % Change"
        else:
            label = self.label
        
        # Default to percentage format if not specified
        value_format = self.value_format or "percent"
        
        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Get the base year value (first year)
        base_year = model.years[0]
        base_value = model[self.name, base_year]
        
        # Add cells for each year with cumulative percent change calculation
        for year in model.years:
            current_value = model[self.name, year]
            
            # Calculate cumulative percent change from base year
            if base_value is None or current_value is None or base_value == 0:
                cumulative_percent_change = None
            else:
                cumulative_percent_change = (current_value - base_value) / base_value
            
            cells.append(Cell(value=cumulative_percent_change, bold=self.bold, value_format=value_format))
        
        return Row(cells=cells)


@dataclass
class ConstraintPassRow(BaseRow):
    """Configuration for constraint pass/fail row generation."""
    constraint_name: str
    pass_msg: str = "Pass"
    fail_msg: str = "Fail"
    label: Optional[str] = None
    color_code: bool = False
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing constraint evaluation results across all years."""
        # Get the constraint object
        constraint = model.get_constraint_definition(self.constraint_name)
        
        # Use constraint name as label if no custom label provided
        label = self.label or self.constraint_name
        
        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Add cells for each year with constraint evaluation result
        for year in model.years:
            try:
                is_satisfied = constraint.evaluate(model._value_matrix, year)
                result_msg = self.pass_msg if is_satisfied else self.fail_msg
                
                # Apply background color if color_code is True
                background_color = None
                if self.color_code:
                    background_color = 'lightgreen' if is_satisfied else 'lightcoral'
                
                cells.append(Cell(value=result_msg, bold=self.bold, align='center', background_color=background_color))
            except Exception as e:
                # If evaluation fails, show error message
                cells.append(Cell(value=f"Error: {str(e)}", bold=self.bold, align='center'))
        
        return Row(cells=cells)


@dataclass
class ConstraintVarianceRow(BaseRow):
    """Configuration for constraint variance row generation."""
    constraint_name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing constraint variance (actual - target) across all years."""
        # Get the constraint object
        constraint = model.get_constraint_definition(self.constraint_name)
        
        # Use constraint name with "Variance" suffix as label if no custom label provided
        label = self.label or f"{self.constraint_name} Variance"
        
        # Default to same format as the constraint's target line item if not specified
        value_format = self.value_format or model.line_item(constraint.line_item_name).value_format

        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Add cells for each year with constraint variance calculation
        for year in model.years:
            try:
                variance = constraint.variance(model._value_matrix, year)
                cells.append(Cell(value=variance, bold=self.bold, value_format=value_format))
            except Exception as e:
                # If variance calculation fails, show error message
                cells.append(Cell(value=f"Error: {str(e)}", bold=self.bold, align='center'))
        
        return Row(cells=cells)


@dataclass
class ConstraintTargetRow(BaseRow):
    """Configuration for constraint target row generation."""
    constraint_name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row showing constraint target values across all years."""
        # Get the constraint object
        constraint = model.get_constraint_definition(self.constraint_name)
        
        # Use constraint name with "Target" suffix as label if no custom label provided
        label = self.label or f"{self.constraint_name} Target"
        
        # Default to same format as the constraint's target line item if not specified
        value_format = self.value_format or model.line_item(constraint.line_item_name).value_format

        # Create cells for this row
        cells = []
        if self.include_name:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align='left'))
        cells.append(Cell(value=label, bold=self.bold, align='left'))
        
        # Add cells for each year with constraint target value
        for year in model.years:
            try:
                target_value = constraint.get_target(year)
                cells.append(Cell(value=target_value, bold=self.bold, value_format=value_format))
            except Exception as e:
                # If target retrieval fails, show error message
                cells.append(Cell(value=f"Error: {str(e)}", bold=self.bold, align='center'))
        
        return Row(cells=cells)


@dataclass
class LabelRow(BaseRow):
    """Configuration for label row generation."""
    label: str
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a row with just a label in the leftmost column and empty cells for all years."""
        # Create cells for this row
        cells = [Cell(value=self.label, bold=self.bold, align='left')]
        if self.include_name:
            cells.append(Cell(value=""))
        
        # Add empty cells for each year
        for year in model.years:
            cells.append(Cell(value=""))
        
        return Row(cells=cells)


@dataclass
class BlankRow(BaseRow):
    """Configuration for blank row generation."""
    include_name: bool = False
    bold: bool = False
    
    def generate_row(self, model: 'Model') -> Row:
        """Create a blank row with empty cells for each column."""
        # Create empty cells - one for the label column and one for each year
        cells = [Cell(value="")]  # First cell is empty
        if self.include_name:
            cells.append(Cell(value=""))
        
        # Add empty cell for each year
        for _ in model.years:
            cells.append(Cell(value=""))
        
        return Row(cells=cells)


# Type alias for all row config types
RowConfig = Union[
    ItemRow,
    ItemsByCategoryRow,
    PercentChangeRow,
    CumulativeChangeRow,
    CumulativePercentChangeRow,
    ConstraintPassRow,
    ConstraintVarianceRow,
    ConstraintTargetRow,
    LabelRow,
    BlankRow
]


def dict_to_row_config(data: dict) -> RowConfig:
    """Convert a dictionary to the appropriate row config dataclass."""
    row_type = data.get('type')
    config_data = {k: v for k, v in data.items() if k != 'type'}
    
    if row_type == 'item':
        return ItemRow(**config_data)
    elif row_type == 'items_by_category':
        return ItemsByCategoryRow(**config_data)
    elif row_type == 'percent_change':
        return PercentChangeRow(**config_data)
    elif row_type == 'cumulative_change':
        return CumulativeChangeRow(**config_data)
    elif row_type == 'cumulative_percent_change':
        return CumulativePercentChangeRow(**config_data)
    elif row_type == 'constraint_pass':
        return ConstraintPassRow(**config_data)
    elif row_type == 'constraint_variance':
        return ConstraintVarianceRow(**config_data)
    elif row_type == 'constraint_target':
        return ConstraintTargetRow(**config_data)
    elif row_type == 'label':
        return LabelRow(**config_data)
    elif row_type == 'blank':
        return BlankRow(**config_data)
    else:
        raise ValueError(f"Unknown row type: {row_type}")
