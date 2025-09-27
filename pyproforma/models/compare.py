"""
Model comparison functionality for analyzing differences between two Model instances.
"""

from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from pyproforma.tables import row_types as rt
from pyproforma.tables.table_class import Table
from pyproforma.tables.table_generator import generate_multi_model_table


class Compare:
    """
    Comparison analysis between two Model instances.

    Provides methods for analyzing differences in values, structure, and performance
    between a base model and a comparison model.
    """

    def __init__(self, base_model, compare_model):
        """
        Initialize comparison between two models.

        Args:
            base_model (Model): The base model for comparison
            compare_model (Model): The model to compare against the base
        """
        self.base_model = base_model
        self.compare_model = compare_model

        # Validate that models have compatible structure for comparison
        self._validate_models()

    def _validate_models(self):
        """Validate that models can be meaningfully compared."""
        # Check that years overlap
        base_years = set(self.base_model.years)
        compare_years = set(self.compare_model.years)

        if not base_years.intersection(compare_years):
            raise ValueError(
                "Models must have at least one overlapping year for comparison"
            )

        self.common_years = sorted(list(base_years.intersection(compare_years)))

        # Get common line items that exist in both models
        base_items = set([item["name"] for item in self.base_model.line_item_metadata])
        compare_items = set(
            [item["name"] for item in self.compare_model.line_item_metadata]
        )

        self.common_items = sorted(list(base_items.intersection(compare_items)))
        self.base_only_items = sorted(list(base_items - compare_items))
        self.compare_only_items = sorted(list(compare_items - base_items))

    def difference(
        self, item_name: str, year: Optional[int] = None
    ) -> Union[float, Dict[int, float]]:
        """
        Calculate absolute difference between models for a specific item and year.

        Args:
            item_name (str): Name of the item to compare
            year (int, optional): Year to compare. If None, returns differences for all common years.

        Returns:
            float: Absolute difference (compare_model - base_model) if year is specified
            dict: Dictionary of year:difference pairs if year is None

        Raises:
            KeyError: If item not found in both models, or if year specified but not found in both models
        """  # noqa: E501
        if item_name not in self.common_items:
            raise KeyError(f"Item '{item_name}' not found in both models")

        if year is None:
            # Return differences for all common years
            result = {}
            for y in self.common_years:
                base_value = self.base_model.value(item_name, y)
                compare_value = self.compare_model.value(item_name, y)

                # Handle None values
                if base_value is None and compare_value is None:
                    result[y] = 0
                elif base_value is None:
                    result[y] = compare_value
                elif compare_value is None:
                    result[y] = -base_value
                else:
                    result[y] = compare_value - base_value
            return result
        else:
            # Return difference for specific year
            if year not in self.common_years:
                raise KeyError(f"Year {year} not found in both models")

            base_value = self.base_model.value(item_name, year)
            compare_value = self.compare_model.value(item_name, year)

            # Handle None values
            if base_value is None and compare_value is None:
                return 0
            elif base_value is None:
                return compare_value
            elif compare_value is None:
                return -base_value

            return compare_value - base_value

    def cumulative_difference(self, item_name: str, year: int) -> float:
        """
        Calculate cumulative difference between models for a specific item up through the specified year.

        Args:
            item_name (str): Name of the item to compare
            year (int): Year up through which to sum differences (inclusive)

        Returns:
            float: Cumulative difference (sum of all differences from first common year through specified year)

        Raises:
            KeyError: If item not found in both models, or if year is before the first common year
        """  # noqa: E501
        if item_name not in self.common_items:
            raise KeyError(f"Item '{item_name}' not found in both models")

        if year < min(self.common_years):
            raise KeyError(
                (
                    f"Year {year} is before the first common year "
                    f"({min(self.common_years)})"
                )
            )

        # Sum differences from first common year through specified year
        cumulative_diff = 0
        for y in self.common_years:
            if y <= year:
                try:
                    diff = self.difference(item_name, y)
                    if diff is not None:
                        cumulative_diff += diff
                except (KeyError, ValueError):
                    # Skip years where we can't calculate difference
                    continue
            else:
                # We've passed the target year, stop summing
                break

        return cumulative_diff

    def percent_difference(self, item_name: str, year: int) -> Optional[float]:
        """
        Calculate percentage difference between models for a specific item and year.

        Args:
            item_name (str): Name of the item to compare
            year (int): Year to compare

        Returns:
            float: Percentage difference as decimal (0.1 = 10% increase)
            None: If base value is zero or either value is None

        Raises:
            KeyError: If item or year not found in both models
        """
        if item_name not in self.common_items:
            raise KeyError(f"Item '{item_name}' not found in both models")
        if year not in self.common_years:
            raise KeyError(f"Year {year} not found in both models")

        base_value = self.base_model.value(item_name, year)
        compare_value = self.compare_model.value(item_name, year)

        # Handle None values or zero base value
        if base_value is None or compare_value is None:
            return None
        if base_value == 0:
            return None

        return (compare_value - base_value) / base_value

    def ratio(self, item_name: str, year: int) -> Optional[float]:
        """
        Calculate ratio of compare_model to base_model for a specific item and year.

        Args:
            item_name (str): Name of the item to compare
            year (int): Year to compare

        Returns:
            float: Ratio (compare_model / base_model)
            None: If base value is zero or either value is None

        Raises:
            KeyError: If item or year not found in both models
        """
        if item_name not in self.common_items:
            raise KeyError(f"Item '{item_name}' not found in both models")
        if year not in self.common_years:
            raise KeyError(f"Year {year} not found in both models")

        base_value = self.base_model.value(item_name, year)
        compare_value = self.compare_model.value(item_name, year)

        # Handle None values or zero base value
        if base_value is None or compare_value is None:
            return None
        if base_value == 0:
            return None

        return compare_value / base_value

    def all_differences(self) -> pd.DataFrame:
        """
        Get a DataFrame showing differences for all common items across all common years.

        Returns:
            pd.DataFrame: DataFrame with items as rows, years as columns, values as differences
        """  # noqa: E501
        data = {}

        for year in self.common_years:
            year_diffs = []
            for item in self.common_items:
                try:
                    diff = self.difference(item, year)
                    year_diffs.append(diff)
                except (KeyError, ValueError):
                    year_diffs.append(None)
            data[year] = year_diffs

        return pd.DataFrame(data, index=self.common_items)

    def structural_changes(self) -> Dict[str, List[str]]:
        """
        Identify structural differences between the models.

        Returns:
            dict: Dictionary with keys 'added_items', 'removed_items', 'formula_changes'
        """
        result = {
            "added_items": self.compare_only_items,
            "removed_items": self.base_only_items,
            "formula_changes": [],
        }

        # Check for formula changes in common line items
        for item_name in self.common_items:
            try:
                # Only check actual line items, not category totals or generators
                base_item_meta = self.base_model._get_item_metadata(item_name)
                compare_item_meta = self.compare_model._get_item_metadata(item_name)

                if (
                    base_item_meta["source_type"] == "line_item"
                    and compare_item_meta["source_type"] == "line_item"
                ):
                    base_line_item = self.base_model._line_item_definition(item_name)
                    compare_line_item = self.compare_model._line_item_definition(
                        item_name
                    )

                    if base_line_item.formula != compare_line_item.formula:
                        result["formula_changes"].append(item_name)
            except (KeyError, AttributeError):
                # Skip if we can't access line item definitions
                continue

        return result

    def category_difference(self, category_name: str) -> Dict[int, float]:
        """
        Compare category totals between models.

        Args:
            category_name (str): Name of the category to compare

        Returns:
            dict: Dictionary mapping year to difference in category totals

        Raises:
            KeyError: If category not found in both models
        """
        differences = {}

        for year in self.common_years:
            try:
                base_total = self.base_model.category_total(category_name, year)
                compare_total = self.compare_model.category_total(category_name, year)
                differences[year] = compare_total - base_total
            except KeyError:
                # Category might not exist in one of the models
                differences[year] = None

        return differences

    def largest_changes(
        self, n: int = 10, metric: str = "absolute"
    ) -> List[Tuple[str, int, float]]:
        """
        Find the items with the largest changes between models.

        Args:
            n (int): Number of top changes to return
            metric (str): Type of change to measure ('absolute', 'percent')

        Returns:
            list: List of tuples (item_name, year, change_value) sorted by magnitude
        """
        changes = []

        for item in self.common_items:
            for year in self.common_years:
                try:
                    if metric == "absolute":
                        change = abs(self.difference(item, year))
                        if change is not None:
                            changes.append((item, year, change))
                    elif metric == "percent":
                        pct_change = self.percent_difference(item, year)
                        if pct_change is not None:
                            changes.append((item, year, abs(pct_change)))
                except (KeyError, ValueError):
                    continue

        # Sort by magnitude (descending) and return top n
        changes.sort(key=lambda x: x[2], reverse=True)
        return changes[:n]

    def summary_stats(self) -> Dict[str, Union[int, float, List[str]]]:
        """
        Get overall statistics about the comparison.

        Returns:
            dict: Summary statistics including counts, totals, and item lists
        """
        all_diffs = self.all_differences()

        # Calculate summary statistics
        total_abs_diff = all_diffs.abs().sum().sum()
        mean_abs_diff = all_diffs.abs().mean().mean()

        # Count significant changes (>5% or >1000 absolute)
        significant_changes = []
        for item in self.common_items:
            for year in self.common_years:
                try:
                    abs_diff = abs(self.difference(item, year))
                    pct_diff = self.percent_difference(item, year)

                    if (abs_diff and abs_diff > 1000) or (
                        pct_diff and abs(pct_diff) > 0.05
                    ):
                        significant_changes.append(f"{item} ({year})")
                except (KeyError, ValueError, TypeError):
                    continue

        return {
            "common_items_count": len(self.common_items),
            "common_years_count": len(self.common_years),
            "items_added": len(self.compare_only_items),
            "items_removed": len(self.base_only_items),
            "total_absolute_difference": total_abs_diff,
            "mean_absolute_difference": mean_abs_diff,
            "significant_changes_count": len(significant_changes),
            "significant_changes": significant_changes[:10],  # Show first 10
            "structural_changes": self.structural_changes(),
        }

    def to_dataframe(self, metric: str = "difference") -> pd.DataFrame:
        """
        Export comparison data to a structured DataFrame.

        Args:
            metric (str): Type of comparison ('difference', 'percent_difference', 'ratio')

        Returns:
            pd.DataFrame: DataFrame with comparison data
        """  # noqa: E501
        if metric == "difference":
            return self.all_differences()

        data = {}
        for year in self.common_years:
            year_values = []
            for item in self.common_items:
                try:
                    if metric == "percent_difference":
                        value = self.percent_difference(item, year)
                    elif metric == "ratio":
                        value = self.ratio(item, year)
                    else:
                        raise ValueError(f"Unknown metric: {metric}")
                    year_values.append(value)
                except (KeyError, ValueError):
                    year_values.append(None)
            data[year] = year_values

        return pd.DataFrame(data, index=self.common_items)

    def report(self) -> str:
        """
        Generate a formatted text summary of key differences.

        Returns:
            str: Formatted report string
        """
        stats = self.summary_stats()
        structural = stats["structural_changes"]

        report = f"""
Model Comparison Report
======================

Overview:
- Common items: {stats["common_items_count"]}
- Common years: {stats["common_years_count"]}
- Items added: {stats["items_added"]}
- Items removed: {stats["items_removed"]}

Structural Changes:
- Formula changes: {len(structural["formula_changes"])}
"""

        if structural["formula_changes"]:
            report += (
                f"  Changed formulas: {', '.join(structural['formula_changes'][:5])}"
            )
            if len(structural["formula_changes"]) > 5:
                report += f" (and {len(structural['formula_changes']) - 5} more)"
            report += "\n"

        if structural["added_items"]:
            report += f"- Added items: {', '.join(structural['added_items'][:5])}"
            if len(structural["added_items"]) > 5:
                report += f" (and {len(structural['added_items']) - 5} more)"
            report += "\n"

        if structural["removed_items"]:
            report += f"- Removed items: {', '.join(structural['removed_items'][:5])}"
            if len(structural["removed_items"]) > 5:
                report += f" (and {len(structural['removed_items']) - 5} more)"
            report += "\n"

        report += f"""
Financial Impact:
- Total absolute difference: {stats["total_absolute_difference"]:,.2f}
- Mean absolute difference: {stats["mean_absolute_difference"]:,.2f}
- Significant changes: {stats["significant_changes_count"]}

Top Changes:
"""

        top_changes = self.largest_changes(5)
        for item, year, change in top_changes:
            report += f"- {item} ({year}): {change:,.2f}\n"

        return report

    def difference_table(
        self, item_name: Union[str, List[str]], include_cumulative: bool = False
    ) -> Table:
        """
        Generate a table comparing base and compare model values for specific item(s).

        Args:
            item_name (str or list): Name of the item to compare, or list of item names
            include_cumulative (bool): If True, includes a row showing cumulative differences

        Returns:
            Table: A formatted table with rows for each item showing base model values,
                   compare model values, and differences

        Raises:
            KeyError: If any item not found in both models
        """  # noqa: E501
        # Handle both single item and list of items
        if isinstance(item_name, str):
            item_names = [item_name]
        else:
            item_names = item_name

        # Validate all items exist in both models
        for name in item_names:
            if name not in self.common_items:
                raise KeyError(f"Item '{name}' not found in both models")

        model_row_pairs = []

        for i, name in enumerate(item_names):
            # Add blank row between items (except before the first item)
            if i > 0:
                blank_row = rt.BlankRow()
                model_row_pairs.append((self.base_model, blank_row))

            item_label = self.base_model.line_item(name).label
            item_value_format = self.base_model.line_item(name).value_format
            label_row = rt.LabelRow(label=item_label, bold=True)

            # Create row configurations for base and compare models
            base_row = rt.ItemRow(name=name, label="Base Model", bold=False)
            compare_row = rt.ItemRow(name=name, label="Compare Model", bold=False)

            # Calculate differences for all common years
            differences_dict = {}
            for year in self.common_years:
                try:
                    diff = self.difference(name, year)
                    differences_dict[year] = diff
                except (KeyError, ValueError):
                    differences_dict[year] = None

            # Create custom row for differences
            difference_row = rt.CustomRow(
                label="Difference",
                values=differences_dict,
                value_format=item_value_format,
                bold=True,
            )

            # Create cumulative difference row if requested
            cumulative_row = None
            if include_cumulative:
                cumulative_dict = {}
                for year in self.common_years:
                    try:
                        cumulative_diff = self.cumulative_difference(name, year)
                        cumulative_dict[year] = cumulative_diff
                    except (KeyError, ValueError):
                        cumulative_dict[year] = None

                cumulative_row = rt.CustomRow(
                    label="Cumulative",
                    values=cumulative_dict,
                    value_format=item_value_format,
                    bold=True,
                )

            # Add rows for this item
            rows_to_add = [
                (self.base_model, label_row),
                (self.base_model, base_row),
                (self.compare_model, compare_row),
                (self.base_model, difference_row),  # Use base_model for years structure
            ]

            if include_cumulative and cumulative_row:
                rows_to_add.append((self.base_model, cumulative_row))

            model_row_pairs.extend(rows_to_add)

        # Generate the table using the multi-model table generator
        table = generate_multi_model_table(model_row_pairs)

        return table

    def __repr__(self) -> str:
        """String representation of the comparison."""
        return (
            f"Compare({len(self.common_items)} common items, "
            f"{len(self.common_years)} common years)"
        )
