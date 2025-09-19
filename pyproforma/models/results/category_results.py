from typing import TYPE_CHECKING, Optional

import pandas as pd

from pyproforma.tables.table_class import Table

if TYPE_CHECKING:
    from ..model import Model


class CategoryResults:
    """
    A helper class that provides convenient methods for exploring and summarizing
    line items within a specific category of a financial model.

    This class is typically instantiated through the Model.category() method and
    provides an intuitive interface for notebook exploration and analysis.

    Args:
        model: The parent Model instance
        category_name: The name of the category to analyze

    Examples:
        >>> revenue_results = model.category('revenue')
        >>> print(revenue_results)  # Shows summary info
        >>> revenue_results.total()  # Returns dict of year: total
        >>> revenue_results.items  # Returns list of LineItems
        >>> revenue_results.to_dataframe()  # Returns pandas DataFrame
    """

    def __init__(self, model: "Model", category_name: str):
        self.model = model
        self.category_name = category_name
        self.category_metadata = model._get_category_metadata(category_name)
        if self.category_metadata["system_generated"] is False:
            self.category_obj = model.category_definition(category_name)
        else:
            self.category_obj = None
        self.line_item_names = model.line_item_names_by_category(category_name)

    @property
    def name(self) -> str:
        """The category name."""
        return self.category_metadata["name"]

    @property
    def label(self) -> str:
        """The display label for the category."""
        return self.category_metadata["label"]

    @property
    def include_total(self) -> bool:
        """Whether the category includes a total row."""
        return self.category_metadata["include_total"]

    @property
    def total_name(self) -> str:
        """The name used for the category total."""
        return self.category_metadata["total_name"]

    @property
    def total_label(self) -> str:
        """The display label for the category total."""
        return self.category_metadata["total_label"]

    @property
    def system_generated(self) -> bool:
        """Whether the category was auto-generated."""
        return self.category_metadata["system_generated"]

    def __str__(self) -> str:
        """
        Return a string representation showing key information about the category.
        """
        return self.summary()

    def __repr__(self) -> str:
        return (
            f"CategoryResults(category_name='{self.category_name}', "
            f"num_items={len(self.line_item_names)})"
        )

    def totals(self) -> dict[int, float]:
        """
        Return a dictionary of year: total value for this category.

        Returns:
            dict[int, float]: Dictionary mapping years to category totals

        Raises:
            ValueError: If the category doesn't include totals
        """
        if not self.include_total:
            raise ValueError(f"Category '{self.category_name}' does not include totals")

        totals = {}
        for year in self.model.years:
            try:
                totals[year] = self.model.category_total(self.category_name, year)
            except KeyError:
                totals[year] = 0.0

        return totals

    def values(self) -> dict[str, dict[int, float]]:
        """
        Return a nested dictionary of item_name: {year: value} for all items in category.

        Returns:
            dict[str, dict[int, float]]: Nested dictionary with values for each item by year
        """  # noqa: E501
        values = {}
        for item_name in self.line_item_names:
            values[item_name] = {}
            for year in self.model.years:
                try:
                    values[item_name][year] = self.model.value(item_name, year)
                except KeyError:
                    values[item_name][year] = 0.0

        return values

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return a pandas DataFrame with line items as rows and years as columns.

        Returns:
            pd.DataFrame: DataFrame with line items and their values across years
        """
        values_dict = self.values()

        # Create DataFrame with line items as index and years as columns
        df_data = {}
        for year in self.model.years:
            df_data[year] = [
                values_dict[item_name][year] for item_name in self.line_item_names
            ]

        df = pd.DataFrame(df_data, index=self.line_item_names)

        # Add total row if category includes totals
        if self.include_total:
            try:
                total_row = self.totals()
                df.loc[self.total_name] = [total_row[year] for year in self.model.years]
            except (ValueError, KeyError):
                pass

        return df

    def table(self, hardcoded_color: Optional[str] = None) -> Table:
        """
        Return a Table object for this category using the tables.category() function.

        Args:
            hardcoded_color (Optional[str]): CSS color string to use for hardcoded values.
                                           If provided, cells with hardcoded values will be
                                           displayed in this color. Defaults to None.

        Returns:
            Table: A Table object containing the category items formatted for display
        """  # noqa: E501
        return self.model.tables.category(
            self.category_name, hardcoded_color=hardcoded_color
        )

    def _repr_html_(self) -> str:
        """
        Return HTML representation for Jupyter notebooks.
        This ensures proper formatting when the object is displayed in a notebook cell.
        """
        return self.summary(html=True)

    def summary(self, html: bool = False) -> str:
        """
        Return a summary string with key statistics about the category.

        Args:
            html (bool, optional): If True, returns HTML formatted output. Defaults to False.

        Returns:
            str: Formatted summary of the category
        """  # noqa: E501
        num_items = len(self.line_item_names)
        item_names = self.line_item_names

        # Get totals for all years if category includes totals
        total_info = ""
        if self.include_total and self.model.years:
            try:
                totals_list = []
                for year in self.model.years:
                    total_value = self.model.category_total(self.category_name, year)
                    formatted_total = f"{total_value:,.0f}"
                    totals_list.append(formatted_total)
                total_info = f"\nTotals: {', '.join(totals_list)}"
            except (KeyError, AttributeError):
                total_info = "\nTotals: Not available"

        summary_text = (
            f"CategoryResults('{self.category_name}')\n"
            f"Label: {self.label}\n"
            f"Line Items: {num_items}\n"
            f"Items: {', '.join(item_names)}{total_info}"
        )

        if html:
            html_summary = summary_text.replace("\n", "<br>")
            return f"<pre>{html_summary}</pre>"
        else:
            return summary_text
