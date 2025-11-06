"""
Year-over-year comparison table generation.
"""

from typing import TYPE_CHECKING, Optional

from .table_class import Cell, Column, Row, Table

if TYPE_CHECKING:
    from pyproforma import Model


def compare_years(
    model: "Model",
    year1: int,
    year2: int,
    names: Optional[list[str]] = None,
    include_change: bool = True,
    include_percent_change: bool = True,
    sort_by: Optional[str] = None,
) -> Table:
    """
    Create a comparison table between two years.

    Args:
        model (Model): The model to generate the table from
        year1 (int): The first year to compare
        year2 (int): The second year to compare
        names (Optional[list[str]]): List of line item names to include.
                                   If None, includes all line items. Defaults to None.
        include_change (bool): Whether to include the Change column. Defaults to True.
        include_percent_change (bool): Whether to include the Percent Change column.
                                     Defaults to True.
        sort_by (Optional[str]): How to sort the items.
                               Options: None, 'value', 'change', 'percent_change'.
                               None keeps the original order. Defaults to None.

    Returns:
        Table: A table with columns for year1, year2, and optional change columns

    Raises:
        ValueError: If year1 or year2 are not in the model's years, or if sort_by
                   is invalid
    """
    # If names is None, use all line items
    if names is None:
        names = [item["name"] for item in model.line_item_metadata]

    prev_year = year1
    year = year2

    # Validate years exist
    if prev_year not in model.years:
        raise ValueError(
            f"Year {prev_year} not found in model years: {model.years}"
        )
    if year not in model.years:
        raise ValueError(f"Year {year} not found in model years: {model.years}")

    # Validate sort_by
    valid_sort_options = [None, "value", "change", "percent_change"]
    if sort_by not in valid_sort_options:
        raise ValueError(
            f"Invalid sort_by value: '{sort_by}'. Must be one of: {valid_sort_options}"
        )

    # Build columns
    columns = [
        Column(label="Item", text_align="left"),
        Column(label=prev_year, value_format="year"),
        Column(label=year, value_format="year"),
    ]

    if include_change:
        columns.append(Column(label="Change"))

    if include_percent_change:
        columns.append(Column(label="% Change"))

    # Collect data for each item
    items_data = []
    for name in names:
        # Get line item for label and value format
        line_item = model.line_item(name)
        label = line_item.label
        value_format = line_item.value_format

        # Get values
        prev_value = model.value(name, prev_year)
        curr_value = model.value(name, year)

        # Calculate change
        change = None
        if prev_value is not None and curr_value is not None:
            change = curr_value - prev_value
        elif curr_value is not None:
            change = curr_value
        elif prev_value is not None:
            change = -prev_value

        # Calculate percent change
        percent_change = None
        if prev_value is not None and curr_value is not None and prev_value != 0:
            percent_change = (curr_value - prev_value) / prev_value

        items_data.append(
            {
                "name": name,
                "label": label,
                "prev_value": prev_value,
                "curr_value": curr_value,
                "change": change,
                "percent_change": percent_change,
                "value_format": value_format,
            }
        )

    # Sort if requested
    if sort_by == "value":
        items_data.sort(key=lambda x: x["curr_value"] or 0, reverse=True)
    elif sort_by == "change":
        items_data.sort(
            key=lambda x: abs(x["change"]) if x["change"] is not None else 0,
            reverse=True,
        )
    elif sort_by == "percent_change":
        items_data.sort(
            key=lambda x: (
                abs(x["percent_change"]) if x["percent_change"] is not None else 0
            ),
            reverse=True,
        )

    # Build rows
    rows = []
    total_prev = 0
    total_curr = 0
    total_change = 0

    for item in items_data:
        cells = [
            Cell(value=item["label"], align="left"),
            Cell(value=item["prev_value"], value_format=item["value_format"]),
            Cell(value=item["curr_value"], value_format=item["value_format"]),
        ]

        if include_change:
            cells.append(Cell(value=item["change"], value_format=item["value_format"]))

        if include_percent_change:
            cells.append(
                Cell(value=item["percent_change"], value_format="percent_one_decimal")
            )

        rows.append(Row(cells=cells))

        # Accumulate totals
        if item["prev_value"] is not None:
            total_prev += item["prev_value"]
        if item["curr_value"] is not None:
            total_curr += item["curr_value"]
        if item["change"] is not None:
            total_change += item["change"]

    # Calculate total percent change
    total_percent_change = None
    if total_prev != 0:
        total_percent_change = (total_curr - total_prev) / total_prev

    # Add total row
    total_cells = [
        Cell(value="Total", align="left", bold=True, top_border="single"),
        Cell(
            value=total_prev,
            value_format="no_decimals",
            bold=True,
            top_border="single",
        ),
        Cell(
            value=total_curr,
            value_format="no_decimals",
            bold=True,
            top_border="single",
        ),
    ]

    if include_change:
        total_cells.append(
            Cell(
                value=total_change,
                value_format="no_decimals",
                bold=True,
                top_border="single",
            )
        )

    if include_percent_change:
        total_cells.append(
            Cell(
                value=total_percent_change,
                value_format="percent_one_decimal",
                bold=True,
                top_border="single",
            )
        )

    rows.append(Row(cells=total_cells))

    return Table(columns=columns, rows=rows)
