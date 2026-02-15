"""
Tables class for PyProforma v2 API.

Provides table creation methods for v2 models, similar to the v1 API but
adapted for v2's simpler structure.
"""

from typing import TYPE_CHECKING, Optional, Union

from pyproforma.table import Cell, Table

from . import row_types as rt
from .row_types import BaseRow, dict_to_row_config

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel


class Tables:
    """
    A namespace for table creation methods within a PyProforma v2 model.

    The Tables class provides an interface for generating tables from v2 models.
    It serves as the primary entry point for creating formatted tables that display
    model data, including line items and custom templates.

    This class is accessed through a ProformaModel instance's `tables` attribute
    and provides methods to generate tables for different aspects of the model.

    Attributes:
        _model (ProformaModel): The underlying v2 model containing the data
            and definitions used for table generation.

    Examples:
        >>> model = MyModel(periods=[2024, 2025])
        >>> table = model.tables.line_items()
    """

    def __init__(self, model: "ProformaModel"):
        """Initialize the tables namespace with a v2 ProformaModel."""
        self._model = model

    def from_template(
        self,
        template: list[Union[dict, BaseRow]],
        col_labels: Optional[str | list[str]] = None,
    ) -> Table:
        """
        Generate a table from a template of row configurations.

        Args:
            template (list[Union[dict, BaseRow]]): A list of row configuration
                dictionaries or BaseRow instances that define the structure and
                content of the table.
            col_labels: String or list of strings for label columns. Defaults to None.
                If None, defaults to "Name" for single column or ["Name", "Label"]
                for two columns.

        Returns:
            Table: A Table object containing the rows and data as specified by the template.

        Examples:
            >>> template = [
            ...     {"row_type": "label", "label": "Income Statement", "bold": True},
            ...     {"row_type": "item", "name": "revenue"},
            ...     {"row_type": "item", "name": "expenses"},
            ...     {"row_type": "blank"},
            ...     {"row_type": "line_items_total", "line_item_names": ["revenue", "expenses"]},
            ... ]
            >>> table = model.tables.from_template(template)
        """
        # Check if model has periods defined
        if not self._model.periods:
            raise ValueError(
                "Cannot generate table: model has no periods defined. "
                "Please add periods to the model before generating tables."
            )

        # Determine label column count from col_labels
        if col_labels is None:
            # Default to single label column showing name
            label_col_count = 1
            col_labels = "Name"
        elif isinstance(col_labels, str):
            label_col_count = 1
        else:
            label_col_count = len(col_labels)

        # Build header row
        header_cells = []

        # Add label column headers
        if isinstance(col_labels, str):
            header_cells.append(Cell(value=col_labels, bold=True, align="left"))
        else:
            for label in col_labels:
                header_cells.append(Cell(value=label, bold=True, align="left"))

        # Add period column headers
        for period in self._model.periods:
            header_cells.append(
                Cell(value=period, bold=True, align="center", value_format=None)
            )

        # Create data rows
        data_rows = []
        for config in template:
            # Convert dict to dataclass if needed
            if isinstance(config, dict):
                config = dict_to_row_config(config)

            # Generate row(s)
            result = config.generate_row(self._model, label_col_count=label_col_count)
            if isinstance(result, list) and result and isinstance(result[0], list):
                # Multiple rows returned
                data_rows.extend(result)
            else:
                # Single row returned
                data_rows.append(result)

        # Combine header and data rows
        all_rows = [header_cells] + data_rows

        return Table(cells=all_rows)

    def line_items(
        self,
        line_items: Optional[list[str]] = None,
        include_name: bool = True,
        include_label: bool = False,
    ) -> Table:
        """
        Generate a table containing line items.

        Creates a table that displays line items from the model. If no specific
        line items are provided, includes all line items from the model.

        Args:
            line_items (Optional[list[str]]): List of line item names to include.
                If None, includes all line items. Defaults to None.
            include_name (bool): Whether to include the name column. Defaults to True.
            include_label (bool): Whether to include the label column. Defaults to False.

        Returns:
            Table: A Table object containing the specified line items.

        Examples:
            >>> table = model.tables.line_items()
            >>> table = model.tables.line_items(line_items=['revenue', 'expenses'])
            >>> table = model.tables.line_items(include_name=False, include_label=True)
        """
        # Determine which line items to include
        if line_items is None:
            items_to_include = self._model.line_item_names
        else:
            # Validate that all requested items exist
            for item_name in line_items:
                if item_name not in self._model.line_item_names:
                    raise ValueError(
                        f"Line item '{item_name}' not found in model. "
                        f"Available line items: {', '.join(sorted(self._model.line_item_names))}"
                    )
            items_to_include = line_items

        # Determine what to show in the label columns
        show_name = include_name
        show_label = include_label

        # If no label columns specified, default to showing name
        if not show_name and not show_label:
            show_name = True

        # Build col_labels parameter
        col_labels = []
        if show_name:
            col_labels.append("Name")
        if show_label:
            col_labels.append("Label")

        # Build template using ItemRow for each line item
        # When showing only name (not label), explicitly set label=name to override default behavior
        template = []
        for item_name in items_to_include:
            if show_name and not show_label:
                # Force ItemRow to show name instead of label
                template.append(rt.ItemRow(name=item_name, label=item_name))
            else:
                # Let ItemRow use default label behavior
                template.append(rt.ItemRow(name=item_name))

        # Use from_template to generate the table
        return self.from_template(template, col_labels=col_labels)
