"""
Row type configurations for PyProforma v2 API table generation.

This module provides row type classes similar to v1 but adapted for v2 models.
Each row type is a dataclass that can generate table rows from v2 ProformaModel data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel

from pyproforma.table import Cell, Format, NumberFormatSpec


class BaseRow(ABC):
    """Base configuration for all row types in v2."""

    @abstractmethod
    def generate_row(
        self, model: "ProformaModel", label_col_count: int = 1
    ) -> Union[list[Cell], list[list[Cell]]]:
        """Generate row(s) for this configuration.
        
        Args:
            model: The v2 ProformaModel instance
            label_col_count: Number of label columns to include
            
        Returns:
            Either a single list of Cell objects representing one row,
            or a list of lists of Cell objects representing multiple rows.
        """
        pass


@dataclass
class HeaderRow(BaseRow):
    """Configuration for header row generation."""

    col_labels: Union[str, list[str]] = "Name"

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create the header row with label columns and period columns."""
        cells = []

        # Add label column headers
        if isinstance(self.col_labels, str):
            cells.append(Cell(value=self.col_labels, bold=True, align="left"))
        else:
            for label in self.col_labels:
                cells.append(Cell(value=label, bold=True, align="left"))

        # Add period column headers
        for period in model.periods:
            cells.append(
                Cell(value=period, bold=True, align="center", value_format=None)
            )

        return cells


@dataclass
class ItemRow(BaseRow):
    """Configuration for line item row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[Union[str, "NumberFormatSpec", dict]] = None
    bold: bool = False
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row for a line item with its label and values across all periods."""
        # Get the line item result
        item_result = model[self.name]

        # Get label from item or use provided label
        if self.label is not None:
            label = self.label
        elif item_result.label is not None:
            label = item_result.label
        else:
            label = self.name

        # Default value format
        value_format = self.value_format or "no_decimals"

        # Create cells for this row
        cells = []

        # Add label cell(s)
        if label_col_count >= 2:
            # First column: name
            cells.append(
                Cell(
                    value=self.name,
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )
            # Second column: label
            cells.append(
                Cell(
                    value=label,
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )
        else:
            # Single label column
            cells.append(
                Cell(
                    value=label,
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        # Add any additional blank label columns if label_col_count > 2
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Add a cell for each period with the item's value for that period
        for period in model.periods:
            value = item_result[period]
            cells.append(
                Cell(
                    value=value,
                    bold=self.bold,
                    value_format=value_format,
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        return cells


@dataclass
class LabelRow(BaseRow):
    """Configuration for label-only row generation (e.g., section headers)."""

    label: str
    bold: bool = True
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row with just a label spanning label columns."""
        cells = []

        # Add the label in the first label column
        cells.append(
            Cell(
                value=self.label,
                bold=self.bold,
                align="left",
                bottom_border=self.bottom_border,
                top_border=self.top_border,
            )
        )

        # Add blank cells for additional label columns
        for _ in range(label_col_count - 1):
            cells.append(Cell(value=""))

        # Add blank cells for each period
        for _ in model.periods:
            cells.append(Cell(value=""))

        return cells


@dataclass
class BlankRow(BaseRow):
    """Configuration for blank row generation (for spacing)."""

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a completely blank row."""
        cells = []

        # Add blank cells for label columns
        for _ in range(label_col_count):
            cells.append(Cell(value=""))

        # Add blank cells for each period
        for _ in model.periods:
            cells.append(Cell(value=""))

        return cells


@dataclass
class PercentChangeRow(BaseRow):
    """Configuration for percent change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[Union[str, "NumberFormatSpec", dict]] = None
    bold: bool = False

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row showing percent change of a line item from period to period."""
        # Get the line item result
        item_result = model[self.name]

        # Get label
        if self.label is None:
            original_label = item_result.label or self.name
            label = f"{original_label} % Change"
        else:
            label = self.label

        # Default to percentage format
        value_format = self.value_format or Format.PERCENT_TWO_DECIMALS

        # Create cells for this row
        cells = []

        # Add label cell(s)
        if label_col_count >= 2:
            cells.append(Cell(value=self.name, bold=self.bold, align="left"))
            cells.append(Cell(value=label, bold=self.bold, align="left"))
        else:
            cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Calculate percent change for each period
        periods = model.periods
        for i, period in enumerate(periods):
            if i == 0:
                # First period has no previous period
                percent_change = None
            else:
                prev_period = periods[i - 1]
                current_value = item_result[period]
                prev_value = item_result[prev_period]

                if prev_value == 0:
                    percent_change = None
                else:
                    percent_change = (current_value - prev_value) / prev_value

            cells.append(Cell(value=percent_change, bold=self.bold, value_format=value_format))

        return cells


@dataclass
class CumulativeChangeRow(BaseRow):
    """Configuration for cumulative change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[Union[str, "NumberFormatSpec", dict]] = None
    bold: bool = False

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row showing cumulative change of a line item from the base period."""
        # Get the line item result
        item_result = model[self.name]

        # Get label
        if self.label is None:
            original_label = item_result.label or self.name
            label = f"{original_label} Cumulative Change"
        else:
            label = self.label

        # Default to same format as original
        value_format = self.value_format or "no_decimals"

        # Create cells for this row
        cells = []

        # Add label cell(s)
        if label_col_count >= 2:
            cells.append(Cell(value=self.name, bold=self.bold, align="left"))
            cells.append(Cell(value=label, bold=self.bold, align="left"))
        else:
            cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Get base period value
        if model.periods:
            base_period = model.periods[0]
            base_value = item_result[base_period]

            # Calculate cumulative change for each period
            for period in model.periods:
                current_value = item_result[period]
                cumulative_change = current_value - base_value
                cells.append(
                    Cell(value=cumulative_change, bold=self.bold, value_format=value_format)
                )

        return cells


@dataclass
class CumulativePercentChangeRow(BaseRow):
    """Configuration for cumulative percent change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[Union[str, "NumberFormatSpec", dict]] = None
    bold: bool = False

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row showing cumulative percent change from the base period."""
        # Get the line item result
        item_result = model[self.name]

        # Get label
        if self.label is None:
            original_label = item_result.label or self.name
            label = f"{original_label} Cumulative % Change"
        else:
            label = self.label

        # Default to percentage format
        value_format = self.value_format or Format.PERCENT

        # Create cells for this row
        cells = []

        # Add label cell(s)
        if label_col_count >= 2:
            cells.append(Cell(value=self.name, bold=self.bold, align="left"))
            cells.append(Cell(value=label, bold=self.bold, align="left"))
        else:
            cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Get base period value
        if model.periods:
            base_period = model.periods[0]
            base_value = item_result[base_period]

            # Calculate cumulative percent change for each period
            for period in model.periods:
                current_value = item_result[period]

                if base_value == 0:
                    cumulative_percent_change = None
                else:
                    cumulative_percent_change = (current_value - base_value) / base_value

                cells.append(
                    Cell(
                        value=cumulative_percent_change,
                        bold=self.bold,
                        value_format=value_format,
                    )
                )

        return cells


@dataclass
class LineItemsTotalRow(BaseRow):
    """Configuration for row showing the sum of multiple line items."""

    line_item_names: list[str]
    label: str = "Total"
    value_format: Optional[Union[str, "NumberFormatSpec", dict]] = None
    bold: bool = True
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def generate_row(self, model: "ProformaModel", label_col_count: int = 1) -> list[Cell]:
        """Create a row showing the total of specified line items."""
        # Default value format
        value_format = self.value_format or "no_decimals"

        # Create cells for this row
        cells = []

        # Add label cell(s)
        if label_col_count >= 2:
            cells.append(
                Cell(
                    value="",
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )
            cells.append(
                Cell(
                    value=self.label,
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )
        else:
            cells.append(
                Cell(
                    value=self.label,
                    bold=self.bold,
                    align="left",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        # Add blank cells for any additional label columns
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Calculate totals for each period
        for period in model.periods:
            total = sum(model[name][period] for name in self.line_item_names)
            cells.append(
                Cell(
                    value=total,
                    bold=self.bold,
                    value_format=value_format,
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        return cells


# Helper function to convert dict to row config (for backwards compatibility)
def dict_to_row_config(config: dict) -> BaseRow:
    """Convert a dictionary configuration to a BaseRow instance.
    
    Args:
        config: Dictionary with 'row_type' key and corresponding parameters
        
    Returns:
        An instance of the appropriate BaseRow subclass
        
    Raises:
        ValueError: If row_type is unknown or missing
    """
    if "row_type" not in config:
        raise ValueError("Configuration dict must have 'row_type' key")

    row_type = config["row_type"]
    config_copy = config.copy()
    del config_copy["row_type"]

    row_type_map = {
        "header": HeaderRow,
        "item": ItemRow,
        "label": LabelRow,
        "blank": BlankRow,
        "percent_change": PercentChangeRow,
        "cumulative_change": CumulativeChangeRow,
        "cumulative_percent_change": CumulativePercentChangeRow,
        "line_items_total": LineItemsTotalRow,
    }

    if row_type not in row_type_map:
        raise ValueError(
            f"Unknown row_type '{row_type}'. Must be one of: {list(row_type_map.keys())}"
        )

    row_class = row_type_map[row_type]
    return row_class(**config_copy)
