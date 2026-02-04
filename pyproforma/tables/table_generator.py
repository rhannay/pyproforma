from typing import TYPE_CHECKING, Union

from ..table import Cell, Table
from .row_types import BaseRow, dict_to_row_config

if TYPE_CHECKING:
    from pyproforma import Model


class TableGenerationError(Exception):
    """Exception raised when a table cannot be generated."""

    pass


def generate_table_from_template(
    model: "Model",
    template: list[Union[dict, BaseRow]],
    col_labels: Union[str, list[str]] = "Years",
) -> Table:
    """Generate a table from a model using a template specification.

    Args:
        model: The Model instance containing the data
        template: List of row configurations (dicts or dataclass instances)
        col_labels: String or list of strings for label columns

    Returns:
        Table: A formatted table ready for display or export

    Raises:
        TableGenerationError: If model has no years defined
    """
    # Check if years are defined
    if not model.years:
        raise TableGenerationError(
            "Cannot generate table: model has no years defined. "
            "Please add years to the model before generating tables."
        )

    # Build header row
    header_cells = []
    
    # Add label column headers
    if isinstance(col_labels, str):
        header_cells.append(Cell(value=col_labels, bold=True, align="left"))
    else:
        for label in col_labels:
            header_cells.append(Cell(value=label, bold=True, align="left"))

    # Add year column headers
    for year in model.years:
        header_cells.append(Cell(value=year, bold=True, align="center", value_format=None))

    # Create data rows
    data_rows = []
    for config in template:
        # Convert dict to dataclass if needed
        if isinstance(config, dict):
            config = dict_to_row_config(config)

        # Generate row(s)
        result = config.generate_row(model)
        if isinstance(result, list) and result and isinstance(result[0], list):
            # Multiple rows returned
            data_rows.extend(result)
        else:
            # Single row returned
            data_rows.append(result)

    # Combine header and data rows
    all_rows = [header_cells] + data_rows

    return Table(cells=all_rows)


def generate_multi_model_table(model_row_pairs: list[tuple["Model", BaseRow]]) -> Table:
    """Generate a table from multiple models using BaseRow configurations.

    Args:
        model_row_pairs: List of tuples containing (Model, BaseRow) pairs

    Returns:
        Table: A formatted table ready for display or export

    Raises:
        TableGenerationError: If no models provided or all models have empty years
    """
    if not model_row_pairs:
        raise TableGenerationError("Cannot generate table: no models provided.")

    # Collect all unique years from all models and sort them
    all_years = set()
    for model, _ in model_row_pairs:
        all_years.update(model.years)

    if not all_years:
        raise TableGenerationError(
            "Cannot generate table: all models have empty years. "
            "Please add years to at least one model before generating tables."
        )

    sorted_years = sorted(all_years)

    # Build header row - "Year" as first column, then each year
    header_cells = [Cell(value="Year", bold=True, align="left")]
    for year in sorted_years:
        header_cells.append(Cell(value=str(year), bold=True, align="center"))

    # Create data rows
    data_rows = []
    for model, row_config in model_row_pairs:
        # Generate row(s)
        result = row_config.generate_row(model)
        if isinstance(result, list) and result and isinstance(result[0], list):
            # Multiple rows returned
            data_rows.extend(result)
        else:
            # Single row returned
            data_rows.append(result)

    # Combine header and data rows
    all_rows = [header_cells] + data_rows

    return Table(cells=all_rows)
