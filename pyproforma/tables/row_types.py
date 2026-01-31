from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pyproforma import Model

from ..constants import VALID_COLS, ColumnType, ValueFormat
from ..table import Cell, Row


class BaseRow(ABC):
    """Base configuration for all row types."""

    @abstractmethod
    def generate_row(
        self, model: "Model", label_col_count: int = 1
    ) -> Union[Row, list[Row]]:
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
    included_cols: list[ColumnType] = field(default_factory=lambda: ["label"])
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False
    hardcoded_color: Optional[str] = None
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def __post_init__(self):
        """Validate included_cols after initialization."""
        # Validate included_cols
        if not self.included_cols:
            raise ValueError("included_cols cannot be an empty list")

        for col in self.included_cols:
            if col not in VALID_COLS:
                raise ValueError(
                    f"Invalid column '{col}'. Must be one of: {VALID_COLS}"
                )

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row for a line item with its label and values across all years."""
        # Get line_item
        li = model.line_item(self.name)

        # Get label and value format from model if not specified
        label = self.label if self.label is not None else li.label
        value_format = self.value_format or li.value_format

        # Create cells for this row based on included_cols
        cells = []

        # Add cells based on included_cols
        for col in self.included_cols:
            if col == "name":
                cells.append(
                    Cell(
                        value=self.name,
                        bold=self.bold,
                        align="left",
                        bottom_border=self.bottom_border,
                        top_border=self.top_border,
                    )
                )
            elif col == "label":
                cells.append(
                    Cell(
                        value=label,
                        bold=self.bold,
                        align="left",
                        bottom_border=self.bottom_border,
                        top_border=self.top_border,
                    )
                )
            elif col == "category":
                cells.append(
                    Cell(
                        value=li.category,
                        bold=self.bold,
                        align="left",
                        bottom_border=self.bottom_border,
                        top_border=self.top_border,
                    )
                )

        # Add a cell for each year with the item's value for that year
        for year in model.years:
            value = li[year]
            font_color = (
                self.hardcoded_color
                if self.hardcoded_color is not None and li.is_hardcoded(year)
                else None
            )
            cells.append(
                Cell(
                    value=value,
                    bold=self.bold,
                    value_format=value_format,
                    font_color=font_color,
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        return Row(cells=cells)


@dataclass
class ItemsByCategoryRow(BaseRow):
    """Configuration for items by category row generation."""

    category: str
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> list[Row]:
        """Create rows for all line items in a specific category."""
        rows = []
        # Get all line items in the specified category
        for item_name in model.line_item_names_by_category(self.category):
            # Determine included_cols based on label_col_count
            if label_col_count >= 2:
                included_cols = ["name", "label"]
            else:
                included_cols = ["label"]

            item_config = ItemRow(
                name=item_name,
                included_cols=included_cols,
                bold=self.bold,
                value_format=self.value_format,
            )
            rows.append(item_config.generate_row(model, label_col_count))
        return rows


@dataclass
class PercentChangeRow(BaseRow):
    """Configuration for percent change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
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

        # Add label cell
        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for additional label columns (if label_col_count > 1)
        for _ in range(label_col_count - 1):
            cells.append(Cell(value=""))

        # Add cells for each year with percent change calculation
        for year in model.years:
            percent_change = model.line_item(self.name).percent_change(year)
            cells.append(
                Cell(value=percent_change, bold=self.bold, value_format=value_format)
            )

        return Row(cells=cells)


@dataclass
class CumulativeChangeRow(BaseRow):
    """Configuration for cumulative change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
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

        # Add name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value=self.name, bold=self.bold, align="left"))

        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Get the base year value (first year)
        base_year = model.years[0]
        base_value = model.value(self.name, base_year)

        # Add cells for each year with cumulative change calculation
        for year in model.years:
            current_value = model.value(self.name, year)

            # Calculate cumulative change from base year (absolute change)
            if base_value is None or current_value is None:
                cumulative_change = None
            else:
                cumulative_change = current_value - base_value

            cells.append(
                Cell(value=cumulative_change, bold=self.bold, value_format=value_format)
            )

        return Row(cells=cells)


@dataclass
class CumulativePercentChangeRow(BaseRow):
    """Configuration for cumulative percent change row generation."""

    name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing cumulative percent change of a line item from the base year."""  # noqa: E501
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

        # Add name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value=self.name, bold=self.bold, align="left"))

        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Get the base year value (first year)
        base_year = model.years[0]
        base_value = model.value(self.name, base_year)

        # Add cells for each year with cumulative percent change calculation
        for year in model.years:
            current_value = model.value(self.name, year)

            # Calculate cumulative percent change from base year
            if base_value is None or current_value is None or base_value == 0:
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

        return Row(cells=cells)


@dataclass
class ConstraintPassRow(BaseRow):
    """Configuration for constraint pass/fail row generation."""

    constraint_name: str
    pass_msg: str = "Pass"
    fail_msg: str = "Fail"
    label: Optional[str] = None
    color_code: bool = False
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing constraint evaluation results across all years."""
        # Get the constraint results object
        constraint_results = model.constraint(self.constraint_name)

        # Use constraint name as label if no custom label provided
        label = self.label or self.constraint_name

        # Create cells for this row
        cells = []

        # Add name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align="left"))

        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Add cells for each year with constraint evaluation result
        for year in model.years:
            try:
                is_satisfied = constraint_results.evaluate(year)
                result_msg = self.pass_msg if is_satisfied else self.fail_msg

                # Apply background color if color_code is True
                background_color = None
                if self.color_code:
                    background_color = "lightgreen" if is_satisfied else "lightcoral"

                cells.append(
                    Cell(
                        value=result_msg,
                        bold=self.bold,
                        align="center",
                        background_color=background_color,
                    )
                )
            except Exception as e:
                # If evaluation fails, show error message
                cells.append(
                    Cell(value=f"Error: {str(e)}", bold=self.bold, align="center")
                )

        return Row(cells=cells)


@dataclass
class ConstraintVarianceRow(BaseRow):
    """Configuration for constraint variance row generation."""

    constraint_name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing constraint variance (actual - target) across all years."""  # noqa: E501
        # Get the constraint object
        constraint_results = model.constraint(self.constraint_name)

        # Use constraint name with "Variance" suffix as label if no custom label provided  # noqa: E501
        label = self.label or f"{self.constraint_name} Variance"

        # Default to same format as the constraint's target line item if not specified
        value_format = (
            self.value_format
            or model.line_item(constraint_results.line_item_name).value_format
        )

        # Create cells for this row
        cells = []

        # Add name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align="left"))

        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Add cells for each year with constraint variance calculation
        for year in model.years:
            try:
                variance = constraint_results.variance(year)
                cells.append(
                    Cell(value=variance, bold=self.bold, value_format=value_format)
                )
            except Exception as e:
                # If variance calculation fails, show error message
                cells.append(
                    Cell(value=f"Error: {str(e)}", bold=self.bold, align="center")
                )

        return Row(cells=cells)


@dataclass
class ConstraintTargetRow(BaseRow):
    """Configuration for constraint target row generation."""

    constraint_name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing constraint target values across all years."""

        constraint_results = model.constraint(self.constraint_name)

        # Use constraint name with "Target" suffix as label if no custom label provided
        label = self.label or f"{self.constraint_name} Target"

        # Default to same format as the constraint's target line item if not specified
        value_format = (
            self.value_format
            or model.line_item(constraint_results.line_item_name).value_format
        )

        # Create cells for this row
        cells = []

        # Add name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value=self.constraint_name, bold=self.bold, align="left"))

        cells.append(Cell(value=label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Add cells for each year with constraint target value
        for year in model.years:
            try:
                target_value = constraint_results.target_by_year(year)
                cells.append(
                    Cell(value=target_value, bold=self.bold, value_format=value_format)
                )
            except Exception as e:
                # If target retrieval fails, show error message
                cells.append(
                    Cell(value=f"Error: {str(e)}", bold=self.bold, align="center")
                )

        return Row(cells=cells)


@dataclass
class LabelRow(BaseRow):
    """Configuration for label row generation."""

    label: str
    included_cols: list[ColumnType] = field(default_factory=lambda: ["label"])
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row with just a label in the leftmost column and empty cells for all years."""  # noqa: E501
        # Create cells for this row based on included_cols
        cells = []

        # Add cells based on included_cols - put label in first column, empty in others
        for i, col in enumerate(self.included_cols):
            if i == 0:
                # First column gets the label
                cells.append(Cell(value=self.label, bold=self.bold, align="left"))
            else:
                # Other columns are empty
                cells.append(Cell(value="", bold=self.bold, align="left"))

        # Add empty cells for each year
        for year in model.years:
            cells.append(Cell(value=""))

        return Row(cells=cells)


@dataclass
class BlankRow(BaseRow):
    """Configuration for blank row generation."""

    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a blank row with empty cells for each column."""
        # Create empty cells - start with label columns
        cells = []

        # Add empty cells for each label column
        for _ in range(label_col_count):
            cells.append(Cell(value=""))

        # Add empty cell for each year
        for _ in model.years:
            cells.append(Cell(value=""))

        return Row(cells=cells)


@dataclass
class CategoryTotalRow(BaseRow):
    """Configuration for category total row generation."""

    category_name: str
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing category totals across all years."""
        # Get the category results to access the total method
        category_results = model.category(self.category_name)

        # Use provided label or default to category label + "Total"
        if self.label is None:
            label = f"{category_results.label} Total"
        else:
            label = self.label

        # Default to no_decimals format if not specified
        value_format = self.value_format or "no_decimals"

        # Create cells for this row
        cells = []

        # Add empty name cell if we have 2 or more label columns
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
                value=label,
                bold=self.bold,
                align="left",
                bottom_border=self.bottom_border,
                top_border=self.top_border,
            )
        )

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(
                Cell(
                    value="",
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        # Add cells for each year with category total for that year
        for year in model.years:
            total_value = category_results.total(year)
            cells.append(
                Cell(
                    value=total_value,
                    bold=self.bold,
                    value_format=value_format,
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        return Row(cells=cells)


@dataclass
class LineItemsTotalRow(BaseRow):
    """Configuration for line items total row generation."""

    line_item_names: list[str]
    included_cols: list[ColumnType] = field(default_factory=lambda: ["label"])
    label: Optional[str] = None
    value_format: Optional[ValueFormat] = None
    bold: bool = False
    bottom_border: Optional[str] = None
    top_border: Optional[str] = None

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row showing totals for a list of line items across all years.

        The label always appears in the first cell regardless of included_cols
        configuration. All other label columns are empty.
        """
        # Get the line items results to access the total method
        line_items_results = model.line_items(self.line_item_names)

        # Use provided label or default to "Total"
        if self.label is None:
            label = "Total"
        else:
            label = self.label

        # Default to no_decimals format if not specified
        value_format = self.value_format or "no_decimals"

        # Create cells for this row - label always goes in first cell
        cells = []

        # Add cells based on included_cols
        for i, col in enumerate(self.included_cols):
            if i == 0:
                # First column always gets the label, regardless of column type
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
                # All other columns are empty for totals row
                cells.append(
                    Cell(
                        value="",  # Empty for totals row
                        bold=self.bold,
                        align="left",
                        bottom_border=self.bottom_border,
                        top_border=self.top_border,
                    )
                )

        # Add cells for each year with line items total for that year
        for year in model.years:
            total_value = line_items_results.total(year)
            cells.append(
                Cell(
                    value=total_value,
                    bold=self.bold,
                    value_format=value_format,
                    bottom_border=self.bottom_border,
                    top_border=self.top_border,
                )
            )

        return Row(cells=cells)


@dataclass
class CustomRow(BaseRow):
    """Configuration for custom row generation with user-defined values."""

    label: str
    values: dict  # dict of year: float
    value_format: Optional[ValueFormat] = None
    bold: bool = False

    def generate_row(self, model: "Model", label_col_count: int = 1) -> Row:
        """Create a row with custom label and values for specified years."""
        # Create cells for this row
        cells = []

        # Add empty name cell if we have 2 or more label columns
        if label_col_count >= 2:
            cells.append(Cell(value="", bold=self.bold, align="left"))

        cells.append(Cell(value=self.label, bold=self.bold, align="left"))

        # Add blank cells for any additional label columns beyond the first two
        for _ in range(label_col_count - len(cells)):
            cells.append(Cell(value=""))

        # Add a cell for each year with the custom value if available
        for year in model.years:
            value = self.values.get(year, None)
            cells.append(
                Cell(value=value, bold=self.bold, value_format=self.value_format)
            )

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
    BlankRow,
    CategoryTotalRow,
    LineItemsTotalRow,
    CustomRow,
]


def dict_to_row_config(data: dict) -> RowConfig:
    """Convert a dictionary to the appropriate row config dataclass."""
    row_type = data.get("type")
    config_data = {k: v for k, v in data.items() if k != "type"}

    if row_type == "item":
        return ItemRow(**config_data)
    elif row_type == "items_by_category":
        return ItemsByCategoryRow(**config_data)
    elif row_type == "percent_change":
        return PercentChangeRow(**config_data)
    elif row_type == "cumulative_change":
        return CumulativeChangeRow(**config_data)
    elif row_type == "cumulative_percent_change":
        return CumulativePercentChangeRow(**config_data)
    elif row_type == "constraint_pass":
        return ConstraintPassRow(**config_data)
    elif row_type == "constraint_variance":
        return ConstraintVarianceRow(**config_data)
    elif row_type == "constraint_target":
        return ConstraintTargetRow(**config_data)
    elif row_type == "label":
        return LabelRow(**config_data)
    elif row_type == "blank":
        return BlankRow(**config_data)
    elif row_type == "category_total":
        return CategoryTotalRow(**config_data)
    elif row_type == "line_items_total":
        return LineItemsTotalRow(**config_data)
    elif row_type == "custom":
        return CustomRow(**config_data)
    else:
        raise ValueError(f"Unknown row type: {row_type}")
