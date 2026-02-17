"""
Tables class for PyProforma v2 API.

Provides table creation methods for v2 models, similar to the v1 API but
adapted for v2's simpler structure.
"""

from typing import TYPE_CHECKING, Optional, Union

from pyproforma.table import Table

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

        # Determine label column count
        # First check if template has a HeaderRow to get col_labels from
        header_col_labels = None
        for config in template:
            # Convert dict to dataclass if needed for checking
            if isinstance(config, dict):
                temp_config = dict_to_row_config(config)
            else:
                temp_config = config

            if isinstance(temp_config, rt.HeaderRow):
                header_col_labels = temp_config.col_labels
                break

        # Determine label_col_count from HeaderRow if present, otherwise from col_labels param
        if header_col_labels is not None:
            # Use HeaderRow's col_labels
            if isinstance(header_col_labels, str):
                label_col_count = 1
            else:
                label_col_count = len(header_col_labels)
        elif col_labels is None:
            # Default to single label column
            label_col_count = 1
        elif isinstance(col_labels, str):
            label_col_count = 1
        else:
            label_col_count = len(col_labels)

        # Process all rows in template
        all_rows = []
        for config in template:
            # Convert dict to dataclass if needed
            if isinstance(config, dict):
                config = dict_to_row_config(config)

            # Generate row(s)
            result = config.generate_row(self._model, label_col_count=label_col_count)
            if isinstance(result, list) and result and isinstance(result[0], list):
                # Multiple rows returned
                all_rows.extend(result)
            else:
                # Single row returned
                all_rows.append(result)

        return Table(cells=all_rows)

    def line_items(
        self,
        line_items: Optional[list[str]] = None,
        include_name: bool = True,
        include_label: bool = False,
        include_total_row: bool = True,
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
            include_total_row (bool): Whether to include a total row at the bottom.
                Defaults to True.

        Returns:
            Table: A Table object containing the specified line items.

        Examples:
            >>> table = model.tables.line_items()
            >>> table = model.tables.line_items(line_items=['revenue', 'expenses'])
            >>> table = model.tables.line_items(include_name=False, include_label=True)
            >>> table = model.tables.line_items(include_total_row=False)
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

        # Build template starting with HeaderRow
        template = [rt.HeaderRow(col_labels=col_labels)]

        # Add ItemRow for each line item
        # When showing only name (not label), explicitly set label=name to override default behavior
        for item_name in items_to_include:
            if show_name and not show_label:
                # Force ItemRow to show name instead of label
                template.append(rt.ItemRow(name=item_name, label=item_name))
            else:
                # Let ItemRow use default label behavior
                template.append(rt.ItemRow(name=item_name))

        # Add total row if requested and there are items to include
        if include_total_row and items_to_include:
            template.append(
                rt.LineItemsTotalRow(
                    line_item_names=items_to_include,
                    label="Total",
                    bold=True,
                    top_border="single",
                )
            )

        # Use from_template to generate the table
        return self.from_template(template, col_labels=col_labels)

    def line_item(
        self,
        name: str,
        include_name: bool = False,
        include_percent_change: bool = False,
        include_cumulative_change: bool = False,
        include_cumulative_percent_change: bool = False,
    ) -> Table:
        """
        Generate a table for a single line item.

        Creates a table that displays a single line item with its values across all periods.
        Optionally includes analysis rows showing changes over time.

        Args:
            name (str): The name of the line item to display.
            include_name (bool): Whether to include the name column. Defaults to False.
                When False, only the label column is shown.
            include_percent_change (bool): Whether to include a row showing period-over-period
                percent change. Defaults to False.
            include_cumulative_change (bool): Whether to include a row showing cumulative
                change from the base period. Defaults to False.
            include_cumulative_percent_change (bool): Whether to include a row showing
                cumulative percent change from the base period. Defaults to False.

        Returns:
            Table: A Table object containing the line item and any requested analysis rows.

        Raises:
            ValueError: If the line item name doesn't exist in the model.

        Examples:
            >>> table = model.tables.line_item('revenue')
            >>> table = model.tables.line_item('revenue', include_name=True)
            >>> table = model.tables.line_item('revenue', include_percent_change=True)
            >>> table = model.tables.line_item('revenue',
            ...                                 include_cumulative_change=True,
            ...                                 include_cumulative_percent_change=True)
        """
        # Validate that the line item exists
        if name not in self._model.line_item_names:
            raise ValueError(
                f"Line item '{name}' not found in model. "
                f"Available line items: {', '.join(sorted(self._model.line_item_names))}"
            )

        # Build col_labels parameter
        if include_name:
            col_labels = ["Name", "Label"]
        else:
            col_labels = "Label"

        # Build template with HeaderRow and single ItemRow
        template = [
            rt.HeaderRow(col_labels=col_labels),
            rt.ItemRow(name=name),
        ]

        # Add analysis rows if requested
        if include_percent_change:
            template.append(rt.PercentChangeRow(name=name))

        if include_cumulative_change:
            template.append(rt.CumulativeChangeRow(name=name))

        if include_cumulative_percent_change:
            template.append(rt.CumulativePercentChangeRow(name=name))

        # Use from_template to generate the table
        return self.from_template(template, col_labels=col_labels)
