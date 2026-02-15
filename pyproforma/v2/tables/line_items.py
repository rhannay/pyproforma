"""
Line items table creation for PyProforma v2 API.

Provides functions to create tables displaying line items from v2 models.
"""

from typing import TYPE_CHECKING, Optional

from pyproforma.table import Cell, Table

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel


def create_line_items_table(
    model: "ProformaModel",
    line_items: Optional[list[str]] = None,
    include_name: bool = True,
    include_label: bool = False,
) -> Table:
    """
    Create a table displaying line items and their values across periods.

    Args:
        model: The v2 ProformaModel instance
        line_items: List of line item names to include. If None, includes all.
        include_name: Whether to include the name column
        include_label: Whether to include the label column

    Returns:
        Table: A formatted table with line items and their period values

    Examples:
        >>> table = create_line_items_table(model)
        >>> table = create_line_items_table(model, line_items=['revenue', 'expenses'])
    """
    # Determine which line items to include
    if line_items is None:
        items_to_include = model.line_item_names
    else:
        # Validate that all requested items exist
        for item_name in line_items:
            if item_name not in model.line_item_names:
                raise ValueError(
                    f"Line item '{item_name}' not found in model. "
                    f"Available line items: {', '.join(sorted(model.line_item_names))}"
                )
        items_to_include = line_items

    # Build header row
    header_cells = []

    # Add label columns
    if include_name:
        header_cells.append(Cell(value="Name", bold=True, align="left"))
    if include_label:
        header_cells.append(Cell(value="Label", bold=True, align="left"))

    # If no label columns, add a default one
    if not include_name and not include_label:
        header_cells.append(Cell(value="Item", bold=True, align="left"))
        include_name = True  # Default to showing name

    # Add period headers
    for period in model.periods:
        header_cells.append(Cell(value=period, bold=True, align="center"))

    # Build data rows
    data_rows = []
    for item_name in items_to_include:
        row_cells = []

        # Get the line item result for metadata access
        item_result = model[item_name]

        # Add label columns
        if include_name:
            row_cells.append(Cell(value=item_name, align="left"))
        if include_label:
            label = item_result.label if item_result.label else item_name
            row_cells.append(Cell(value=label, align="left"))

        # Add period values
        for period in model.periods:
            value = item_result[period]
            row_cells.append(
                Cell(value=value, align="right", value_format="no_decimals")
            )

        data_rows.append(row_cells)

    # Combine header and data rows
    all_rows = [header_cells] + data_rows

    return Table(cells=all_rows)


def create_line_item_table(
    model: "ProformaModel",
    name: str,
    include_name: bool = False,
) -> Table:
    """
    Create a table for a specific line item showing its values across periods.

    Args:
        model: The v2 ProformaModel instance
        name: The name of the line item
        include_name: Whether to include the name column

    Returns:
        Table: A formatted table with the line item's values

    Examples:
        >>> table = create_line_item_table(model, 'revenue')
        >>> table = create_line_item_table(model, 'revenue', include_name=True)
    """
    # Validate that the line item exists
    if name not in model.line_item_names:
        raise ValueError(
            f"Line item '{name}' not found in model. "
            f"Available line items: {', '.join(sorted(model.line_item_names))}"
        )

    # Build header row
    header_cells = []

    # Add label column
    if include_name:
        header_cells.append(Cell(value="Name", bold=True, align="left"))
    header_cells.append(Cell(value="Label", bold=True, align="left"))

    # Add period headers
    for period in model.periods:
        header_cells.append(Cell(value=period, bold=True, align="center"))

    # Build the single data row
    item_result = model[name]
    row_cells = []

    if include_name:
        row_cells.append(Cell(value=name, align="left"))

    label = item_result.label if item_result.label else name
    row_cells.append(Cell(value=label, align="left"))

    # Add period values
    for period in model.periods:
        value = item_result[period]
        row_cells.append(Cell(value=value, align="right", value_format="no_decimals"))

    # Combine header and data row
    all_rows = [header_cells, row_cells]

    return Table(cells=all_rows)
