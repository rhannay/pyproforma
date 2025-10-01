from typing import TYPE_CHECKING, Optional

from . import row_types as rt
from .table_class import Table
from .table_generator import generate_table_from_template

if TYPE_CHECKING:
    from pyproforma import Model


class Tables:
    """
    A namespace for table creation methods within a Pyproforma model.

    The Tables class provides a comprehensive interface for generating various types
    of tables from a Pyproforma Model. It serves as the primary entry point for
    creating formatted tables that display model data, including line items,
    categories, constraints, and custom templates.

    This class is typically accessed through a Model instance's `tables` attribute
    and provides methods to generate tables for different aspects of the financial
    model, such as individual line items, category summaries, constraint analysis,
    and comprehensive model overviews.

    Attributes:
        _model (Model): The underlying Pyproforma model containing the data
            and definitions used for table generation.

    Examples:
        >>> model = Model(...)  # Initialize with required parameters
        >>> table = model.tables.category('revenue')
    """

    def __init__(self, model: "Model"):
        """Initialize the main tables namespace with a Model."""
        self._model = model

    def from_template(self, template: list[dict], include_name: bool = False) -> Table:
        """
        Generate a table from a template of row configurations.

        Args:
            template (list[dict]): A list of row configuration dictionaries that define
                the structure and content of the table. Each dictionary should specify
                the row type and its parameters (e.g., ItemRow, LabelRow, etc.).
            include_name (bool, optional): Whether to include a name column in the
                generated table. Defaults to False.

        Returns:
            Table: A Table object containing the rows and data as specified by the template.

        Examples:
            >>> template = [
            ...     rt.LabelRow(label='Revenue', bold=True),
            ...     rt.ItemRow(name='sales_revenue'),
            ...     rt.ItemRow(name='other_revenue')
            ... ]
            >>> table = tables.from_template(template, include_name=True)
        """  # noqa: E501
        table = generate_table_from_template(
            self._model, template, include_name=include_name
        )
        return table

    def line_items(
        self, include_name: bool = False, hardcoded_color: Optional[str] = None
    ) -> Table:
        """
        Generate a table containing all line items organized by category.

        Creates a table that displays all line items from the model, organized
        by their respective categories. Each category is shown with a bold header
        followed by its line items, and includes category totals if configured.

        Args:
            include_name (bool, optional): Whether to include the name column. Defaults to False.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing all line items grouped by category.

        Examples:
            >>> table = model.tables.line_items()
            >>> table = model.tables.line_items(include_name=True, hardcoded_color='blue')
        """  # noqa: E501
        rows = self._line_item_rows(hardcoded_color=hardcoded_color)
        return self.from_template(rows, include_name=include_name)

    def _line_item_rows(self, hardcoded_color: Optional[str] = None):
        rows = []
        for category_name in self._model.category_names:
            rows.extend(
                self._category_rows(
                    category_name, hardcoded_color=hardcoded_color
                )
            )
        return rows

    def _category_rows(
        self,
        category_name: str,
        hardcoded_color: Optional[str] = None,
    ):
        rows = []
        category = self._model.category(category_name)
        rows.append(rt.LabelRow(label=category.label, bold=True))

        # Get line item names for this category using metadata
        line_item_names = self._model.line_item_names_by_category(category_name)

        for item_name in line_item_names:
            rows.append(
                rt.ItemRow(
                    name=item_name,
                    hardcoded_color=hardcoded_color,
                )
            )

        return rows

    def category(
        self,
        category_name: str,
        include_name: bool = False,
        hardcoded_color: Optional[str] = None,
    ) -> Table:
        """
        Generate a table for a specific category.

        Args:
            category_name (str): The name of the category to generate the table for.
            include_name (bool, optional): Whether to include the name column. Defaults to False.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the category items.
        """  # noqa: E501
        rows = self._category_rows(
            category_name, hardcoded_color=hardcoded_color
        )
        return self.from_template(rows, include_name=include_name)

    def line_item(
        self,
        name: str,
        include_name: bool = False,
        hardcoded_color: Optional[str] = None,
    ) -> Table:
        """
        Generate a table for a specific line item showing its label and values by year.

        Args:
            name (str): The name of the line item to generate the table for.
            include_name (bool, optional): Whether to include the name column. Defaults to False.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the line item's label and values across years.
        """  # noqa: E501
        rows = [
            rt.ItemRow(name=name, hardcoded_color=hardcoded_color),
            rt.PercentChangeRow(name=name, label="% Change"),
            rt.CumulativeChangeRow(name=name, label="Cumulative Change"),
            rt.CumulativePercentChangeRow(name=name, label="Cumulative % Change"),
        ]
        return self.from_template(rows, include_name=include_name)

    def constraint(self, constraint_name: str, color_code: bool = True) -> Table:
        """
        Generate a table for a specific constraint showing its line item, target, variance, and pass/fail status.

        Args:
            constraint_name (str): The name of the constraint to generate the table for.
            color_code (bool, optional): Whether to apply color coding to the table. Defaults to True.

        Returns:
            Table: A Table object containing the constraint's line item, target, variance, and pass/fail rows.
        """  # noqa: E501
        constraint_results = self._model.constraint(constraint_name)
        rows = [
            rt.LabelRow(label=constraint_results.label, bold=True),
            rt.ItemRow(name=constraint_results.line_item_name),
            rt.ConstraintTargetRow(constraint_name=constraint_name, label="Target"),
            rt.ConstraintVarianceRow(constraint_name=constraint_name, label="Variance"),
            rt.ConstraintPassRow(
                constraint_name=constraint_name,
                label="Pass/Fail",
                color_code=color_code,
            ),
        ]
        return generate_table_from_template(self._model, rows, include_name=False)
