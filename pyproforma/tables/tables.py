"""
Tables — model-aware namespace for building Table objects.

Accessed via model.tables. Takes model data and builds Table instances
via convenience methods (line_item, line_items, precedents) or the general
build() method which accepts a TableDef or plain list of row configurations.

This layer knows about ProformaModel; the Table class beneath it does not.
"""

from typing import TYPE_CHECKING, Optional, Union

from pyproforma.table import Table

from . import row_types as rt
from .row_types import BaseRow, dict_to_row_config

if TYPE_CHECKING:
    from pyproforma.proforma_model import ProformaModel

from pyproforma.line_items.formula_line import FormulaLine


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

    def build(
        self,
        definition: "Union[TableDef, list[Union[dict, BaseRow]]]",
        col_labels: Optional[str | list[str]] = None,
    ) -> Table:
        """
        Build a table from a TableDef or a bare list of row configurations.

        Args:
            definition: Either a TableDef instance or a plain list of row
                configurations (BaseRow instances or equivalent dicts).
            col_labels: String or list of strings for label columns. Defaults to None.

        Returns:
            Table with title populated from TableDef.title when provided.

        Examples:
            >>> model.tables.build(TableDef(rows=[HeaderRow(), ItemRow(name="revenue")],
            ...                             title="Revenue"))
            >>> model.tables.build([HeaderRow(), ItemRow(name="revenue")])
        """
        from pyproforma.tables.table_def import TableDef as _TableDef
        if isinstance(definition, _TableDef):
            title = definition.title
            template = definition.rows
        else:
            title = None
            template = definition

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

        # Build default col_widths: 315px (≈45 Excel units) for label cols,
        # 105px (≈15 Excel units) for each period col
        n_periods = len(self._model.periods)
        col_widths = [245] * label_col_count + [105] * n_periods

        return Table(cells=all_rows, col_widths=col_widths, title=title)

    def line_items(
        self,
        line_items: Optional[list[str]] = None,
        include_name: bool = True,
        include_label: bool = False,
        include_total_row: bool = True,
        hardcoded_color: Optional[str] = None,
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
                template.append(rt.ItemRow(name=item_name, label=item_name, hardcoded_color=hardcoded_color))
            else:
                # Let ItemRow use default label behavior
                template.append(rt.ItemRow(name=item_name, hardcoded_color=hardcoded_color))

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

        # Use build() to generate the table
        return self.build(template, col_labels=col_labels)

    def line_item(
        self,
        name: str,
        include_name: bool = False,
        include_percent_change: bool = False,
        include_cumulative_change: bool = False,
        include_cumulative_percent_change: bool = False,
        hardcoded_color: Optional[str] = None,
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
            rt.ItemRow(name=name, hardcoded_color=hardcoded_color),
        ]

        # Add analysis rows if requested
        if include_percent_change:
            template.append(rt.PercentChangeRow(name=name))

        if include_cumulative_change:
            template.append(rt.CumulativeChangeRow(name=name))

        if include_cumulative_percent_change:
            template.append(rt.CumulativePercentChangeRow(name=name))

        # Use build() to generate the table
        return self.build(template, col_labels=col_labels)

    def precedents(self, name: str, hardcoded_color: Optional[str] = None) -> Table:
        """
        Generate a table showing the precedents of a line item.

        For FormulaLine items, shows each precedent line item followed by a
        bottom border on the last precedent, then the calculated line item in
        bold. For non-formula line items, shows just the single item in bold.

        Only precedents that are themselves line items in the model are shown
        (assumption references are excluded).

        Args:
            name (str): The name of the line item to show precedents for.

        Returns:
            Table: A Table object showing precedents and the calculated result.

        Raises:
            ValueError: If the line item name doesn't exist in the model.

        Examples:
            >>> table = model.tables.precedents('profit')
            >>> table = model.tables.precedents('revenue')  # non-formula: item shown in bold
        """
        if name not in self._model.line_item_names:
            raise ValueError(
                f"Line item '{name}' not found in model. "
                f"Available line items: {', '.join(sorted(self._model.line_item_names))}"
            )

        line_item_def = getattr(self._model.__class__, name)
        template = [rt.HeaderRow(col_labels="Label")]

        if isinstance(line_item_def, FormulaLine) and line_item_def.precedents:
            precedent_names = [
                p for p in line_item_def.precedents
                if p in self._model.line_item_names and p != name
            ]
            for i, precedent_name in enumerate(precedent_names):
                is_last = i == len(precedent_names) - 1
                template.append(rt.ItemRow(
                    name=precedent_name,
                    bottom_border="single" if is_last else None,
                    hardcoded_color=hardcoded_color,
                ))

        template.append(rt.ItemRow(name=name, bold=True, hardcoded_color=hardcoded_color))

        return self.build(template, col_labels="Label")
