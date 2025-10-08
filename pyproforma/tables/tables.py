from typing import TYPE_CHECKING, Optional, Union

from ..constants import VALID_COLS, ColumnType
from . import row_types as rt
from .compare import compare_year as _compare_year
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

    def from_template(
        self, template: list[dict], col_labels: Union[str, list[str]] = "Years"
    ) -> Table:
        """
        Generate a table from a template of row configurations.

        Args:
            template (list[dict]): A list of row configuration dictionaries that define
                the structure and content of the table. Each dictionary should specify
                the row type and its parameters (e.g., ItemRow, LabelRow, etc.).
            col_labels: String or list of strings for label columns. Defaults to "Years".

        Returns:
            Table: A Table object containing the rows and data as specified by the template.

        Examples:
            >>> template = [
            ...     rt.LabelRow(label='Revenue', bold=True),
            ...     rt.ItemRow(name='sales_revenue', included_cols=['label']),
            ...     rt.ItemRow(name='other_revenue', included_cols=['label'])
            ... ]
            >>> table = tables.from_template(template, col_labels="Years")
        """  # noqa: E501
        table = generate_table_from_template(
            self._model, template, col_labels=col_labels
        )
        return table

    def line_items(
        self,
        line_item_names: Optional[list[str]] = None,
        included_cols: list[ColumnType] = ["label"],
        col_labels: Optional[Union[str, list[str]]] = None,
        group_by_category: bool = False,
        include_percent_change: bool = False,
        include_totals: bool = False,
        hardcoded_color: Optional[str] = None,
    ) -> Table:
        """
        Generate a table containing line items with optional category organization.

        Creates a table that displays line items from the model. If no specific
        line items are provided, includes all line items from the model. When
        group_by_category is True, groups items by category with category
        headers.

        Args:
            line_item_names (Optional[list[str]]): List of line item names to include.
                                                  If None, includes all line items. Defaults to None.
            included_cols (list[ColumnType]): List of columns to include. Can contain 'label', 'name',
                                             and/or 'category'. Defaults to ["label"].
            col_labels (Optional[str | list[str]]): Label columns specification. Can be a string
                                                   or list of strings. Defaults to None.
            group_by_category (bool, optional): Whether to group line items by category
                                                     and include category header rows. Defaults to False.
            include_percent_change (bool, optional): Whether to include a percent change row
                                                    after each item row. Defaults to False.
            include_totals (bool, optional): Whether to include a totals row at the end
                                           of the table. Defaults to False.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the specified line items.

        Examples:
            >>> table = model.tables.line_items()
            >>> table = model.tables.line_items(line_item_names=['revenue_sales', 'cost_of_goods'])
            >>> table = model.tables.line_items(included_cols=['name', 'label'], hardcoded_color='blue')
            >>> table = model.tables.line_items(group_by_category=True)
            >>> table = model.tables.line_items(include_percent_change=True)
            >>> table = model.tables.line_items(include_totals=True)
        """  # noqa: E501
        # Validate included_cols
        for col in included_cols:
            if col not in VALID_COLS:
                raise ValueError(
                    f"Invalid column '{col}'. Must be one of: {VALID_COLS}"
                )

        # Set default col_labels if not provided
        if col_labels is None:
            col_labels = included_cols

        # Get line items to include
        if line_item_names is None:
            # Get all line items in their existing order using metadata
            items_metadata = self._model.line_item_metadata.copy()
        else:
            # Filter metadata to only include specified items
            items_metadata = [
                item
                for item in self._model.line_item_metadata
                if item["name"] in line_item_names
            ]

        # Sort by category if we need category labels
        if group_by_category:
            items_metadata = sorted(items_metadata, key=lambda x: x["category"])

        # Create template
        template = []
        current_category = None

        for item in items_metadata:
            # Add category label if needed and this is a new category
            if group_by_category:
                item_category = item["category"]
                if item_category != current_category:
                    # Get category label from model
                    category_metadata = self._model._get_category_metadata(
                        item_category
                    )
                    category_label = category_metadata["label"]

                    template.append(rt.LabelRow(label=category_label, bold=True))
                    current_category = item_category

            # Add the item row
            template.append(
                rt.ItemRow(
                    name=item["name"],
                    included_cols=included_cols,
                    hardcoded_color=hardcoded_color,
                )
            )

            # Add percent change row if requested
            if include_percent_change:
                template.append(rt.PercentChangeRow(name=item["name"]))

        # Add totals row if requested
        if include_totals:
            # Get the list of line item names for the total calculation
            total_line_item_names = [item["name"] for item in items_metadata]
            template.append(
                rt.LineItemsTotalRow(
                    line_item_names=total_line_item_names,
                    bold=True,
                    top_border="single",
                )
            )

        return self.from_template(template, col_labels=col_labels)

    def category(
        self,
        category_name: str,
        include_totals: bool = True,
        hardcoded_color: Optional[str] = None,
    ) -> Table:
        """
        Generate a table for a specific category showing all line items in that category.

        Args:
            category_name (str): The name of the category to generate the table for.
            include_totals (bool, optional): Whether to include a totals row at the end
                                           of the table. Defaults to True.
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing all line items in the specified category.
        """  # noqa: E501
        # Get all line item names for this category
        line_item_names = self._model.line_item_names_by_category(category_name)

        # Use the line_items method if we don't need totals
        if not include_totals:
            return self.line_items(
                line_item_names=line_item_names,
                included_cols=["label"],
                hardcoded_color=hardcoded_color,
            )

        # Create template with line items
        template = []
        for name in line_item_names:
            template.append(
                rt.ItemRow(
                    name=name,
                    included_cols=["label"],
                    hardcoded_color=hardcoded_color,
                )
            )

        # Add category total row if requested
        if include_totals:
            template.append(
                rt.CategoryTotalRow(
                    category_name=category_name,
                    bold=True,
                    top_border="single",
                )
            )

        return self.from_template(template, col_labels=["label"])

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
        # Determine columns to include based on include_name parameter
        cols = ["name", "label"] if include_name else ["label"]

        rows = [
            rt.ItemRow(name=name, included_cols=cols, hardcoded_color=hardcoded_color),
            rt.PercentChangeRow(name=name, label="% Change"),
            rt.CumulativeChangeRow(name=name, label="Cumulative Change"),
            rt.CumulativePercentChangeRow(name=name, label="Cumulative % Change"),
        ]
        return self.from_template(rows)

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
            rt.ItemRow(name=constraint_results.line_item_name, included_cols=["label"]),
            rt.ConstraintTargetRow(constraint_name=constraint_name, label="Target"),
            rt.ConstraintVarianceRow(constraint_name=constraint_name, label="Variance"),
            rt.ConstraintPassRow(
                constraint_name=constraint_name,
                label="Pass/Fail",
                color_code=color_code,
            ),
        ]
        return self.from_template(rows)

    def compare_year(
        self,
        names: list[str],
        year: int,
        include_change: bool = True,
        include_percent_change: bool = True,
        sort_by: Optional[str] = None,
    ) -> Table:
        """
        Create a year-over-year comparison table.

        Args:
            names (list[str]): List of line item names to include
            year (int): The year to compare (will compare year-1 to year)
            include_change (bool): Whether to include the Change column. Defaults to True.
            include_percent_change (bool): Whether to include the Percent Change column. Defaults to True.
            sort_by (Optional[str]): How to sort the items. Options: None, 'value', 'change', 'percent_change'.
                                     None keeps the original order. Defaults to None.

        Returns:
            Table: A table with columns for previous year, current year, and optional change columns

        Raises:
            ValueError: If year or year-1 are not in the model's years, or if sort_by is invalid

        Examples:
            >>> table = model.tables.compare_year(['revenue_sales', 'cost_of_goods'], 2024)
            >>> table = model.tables.compare_year(['revenue_sales'], 2024, sort_by='change')
        """  # noqa: E501
        return _compare_year(
            self._model,
            names,
            year,
            include_change=include_change,
            include_percent_change=include_percent_change,
            sort_by=sort_by,
        )
