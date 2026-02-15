"""
Tables class for PyProforma v2 API.

Provides table creation methods for v2 models, similar to the v1 API but
adapted for v2's simpler structure.
"""

from typing import TYPE_CHECKING, Optional

from pyproforma.table import Table
from pyproforma.tables.table_generator import generate_table_from_template

from .line_items import create_line_items_table

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
        self, template: list[dict], col_labels: Optional[str | list[str]] = None
    ) -> Table:
        """
        Generate a table from a template of row configurations.

        Note: This method uses the v1 table generation infrastructure, which expects
        a v1 Model. For full template support, consider using v1 models or implementing
        v2-specific template handling.

        Args:
            template (list[dict]): A list of row configuration dictionaries that define
                the structure and content of the table.
            col_labels: String or list of strings for label columns. Defaults to None.

        Returns:
            Table: A Table object containing the rows and data as specified by the template.

        Raises:
            NotImplementedError: Template support requires v1-style metadata which v2
                models don't currently provide.
        """
        # For now, this is a placeholder. Full implementation would require
        # either converting v2 models to v1 format or creating v2-specific row types
        raise NotImplementedError(
            "Template-based table generation is not yet supported for v2 models. "
            "Use the line_items() method or individual line item table() methods."
        )

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
        return create_line_items_table(
            self._model,
            line_items=line_items,
            include_name=include_name,
            include_label=include_label,
        )
