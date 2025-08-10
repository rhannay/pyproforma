from .table_class import Table, Column, Row, Cell
from .row_types import BaseRow, RowConfig, dict_to_row_config
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from pyproforma import Model 


def generate_table_from_template(model: 'Model', template: list[Union[dict, BaseRow]], include_name: bool=False) -> Table:
    """Generate a table from a model using a template specification.
    
    Args:
        model: The Model instance containing the data
        template: List of row configurations (dicts or dataclass instances)
        include_name: Whether to include item names in output
        
    Returns:
        Table: A formatted table ready for display or export
    """
    # Create columns - "Year" as first column, then each year in model.years
    columns = [Column(label="Year")]
    if include_name:
        # Add column to make space for name and label
        columns.append(Column(label=""))
    for year in model.years:
        columns.append(Column(label=str(year)))
    
    # Create rows
    rows = []
    for config in template:
        # Convert dict to dataclass if needed
        if isinstance(config, dict):
            config = dict_to_row_config(config)
        
        # Set include_name on the config
        config.include_name = include_name
        
        # Generate row(s)
        result = config.generate_row(model)
        if isinstance(result, list):
            rows.extend(result)
        else:
            rows.append(result)
    
    return Table(columns=columns, rows=rows)

def generate_multi_model_table(model_row_pairs: list[tuple['Model', BaseRow]]) -> Table:
    """Generate a table from multiple models using BaseRow configurations.
    
    Args:
        model_row_pairs: List of tuples containing (Model, BaseRow) pairs
        
    Returns:
        Table: A formatted table ready for display or export
    """
    if not model_row_pairs:
        return Table(columns=[], rows=[])
    
    # Collect all unique years from all models and sort them
    all_years = set()
    for model, _ in model_row_pairs:
        all_years.update(model.years)
    sorted_years = sorted(all_years)
    
    # Create columns - "Year" as first column, then each year
    columns = [Column(label="Year")]
    for year in sorted_years:
        columns.append(Column(label=str(year)))
    
    # Create rows
    rows = []
    for model, row_config in model_row_pairs:
        # # Set include_name to False on the config
        # row_config.include_name = False
        
        # Generate row(s)
        result = row_config.generate_row(model)
        if isinstance(result, list):
            rows.extend(result)
        else:
            rows.append(result)
    
    return Table(columns=columns, rows=rows)