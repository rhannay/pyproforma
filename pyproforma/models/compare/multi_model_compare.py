"""
Multi-model comparison functionality for analyzing differences across
multiple Model instances.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from pyproforma.table import Table
from pyproforma.tables import row_types as rt
from pyproforma.tables.table_generator import generate_multi_model_table

if TYPE_CHECKING:
    from pyproforma import Model

    from .two_model_compare import TwoModelCompare


class MultiModelCompare:
    """
    Comparison analysis across multiple Model instances.

    Provides methods for analyzing differences in values across multiple models.
    """

    def __init__(self, models: List["Model"], labels: Optional[List[str]] = None):
        """
        Initialize comparison across multiple models.

        Args:
            models (List[Model]): List of models to compare (at least 2 required)
            labels (List[str], optional): List of labels for each model.
                If None, uses "Model 1", "Model 2", etc.

        Raises:
            ValueError: If fewer than 2 models are provided
            ValueError: If labels are provided but don't match the number of models
        """
        if len(models) < 2:
            raise ValueError("At least 2 models are required for comparison")

        self.models = models

        # Generate labels if not provided
        if labels is None:
            self.labels = [f"Model {i + 1}" for i in range(len(models))]
        else:
            if len(labels) != len(models):
                raise ValueError(
                    f"Number of labels ({len(labels)}) must match number of "
                    f"models ({len(models)})"
                )
            self.labels = labels

        # Validate that models have compatible structure for comparison
        self._validate_models()

    def _validate_models(self):
        """Validate that models can be meaningfully compared."""
        # Check that all models have at least one year
        for i, model in enumerate(self.models):
            if not model.years:
                raise ValueError(
                    f"Model at index {i} ({self.labels[i]}) has no years defined"
                )

        # Get common years across all models
        common_years_set = set(self.models[0].years)
        for model in self.models[1:]:
            common_years_set = common_years_set.intersection(set(model.years))

        if not common_years_set:
            raise ValueError(
                "Models must have at least one overlapping year for comparison"
            )

        self.common_years = sorted(list(common_years_set))

        # Get common line items that exist in all models
        common_items_set = set(
            [item["name"] for item in self.models[0].line_item_metadata]
        )
        for model in self.models[1:]:
            model_items = set([item["name"] for item in model.line_item_metadata])
            common_items_set = common_items_set.intersection(model_items)

        # Preserve order from first model
        self.common_items = [
            item["name"]
            for item in self.models[0].line_item_metadata
            if item["name"] in common_items_set
        ]

        # Track items unique to each model
        self.unique_items = []
        for i, model in enumerate(self.models):
            model_items = set([item["name"] for item in model.line_item_metadata])
            unique = model_items - common_items_set
            self.unique_items.append(sorted(list(unique)))

    def difference(
        self, item_name: str, year: Optional[int] = None
    ) -> Union[Dict[str, float], Dict[str, Dict[int, float]]]:
        """
        Calculate absolute differences from the first model (baseline) for
        a specific item.

        Args:
            item_name (str): Name of the item to compare
            year (int, optional): Year to compare. If None, returns
                differences for all common years.

        Returns:
            Dict[str, float]: Dictionary of label:difference pairs if year
                is specified
            Dict[str, Dict[int, float]]: Dictionary of label:{year:difference}
                pairs if year is None

        Raises:
            KeyError: If item not found in all models, or if year specified
                but not found in all models
        """
        if item_name not in self.common_items:
            raise KeyError(f"Item '{item_name}' not found in all models")

        if year is None:
            # Return differences for all common years
            result = {}
            for i, (model, label) in enumerate(zip(self.models, self.labels)):
                if i == 0:
                    # First model is the baseline, all differences are 0
                    result[label] = {y: 0.0 for y in self.common_years}
                else:
                    year_diffs = {}
                    for y in self.common_years:
                        base_value = self.models[0].value(item_name, y)
                        compare_value = model.value(item_name, y)

                        # Handle None values
                        if base_value is None and compare_value is None:
                            year_diffs[y] = 0.0
                        elif base_value is None:
                            year_diffs[y] = compare_value
                        elif compare_value is None:
                            year_diffs[y] = -base_value
                        else:
                            year_diffs[y] = compare_value - base_value
                    result[label] = year_diffs
            return result
        else:
            # Return difference for specific year
            if year not in self.common_years:
                raise KeyError(f"Year {year} not found in all models")

            result = {}
            for i, (model, label) in enumerate(zip(self.models, self.labels)):
                if i == 0:
                    # First model is the baseline
                    result[label] = 0.0
                else:
                    base_value = self.models[0].value(item_name, year)
                    compare_value = model.value(item_name, year)

                    # Handle None values
                    if base_value is None and compare_value is None:
                        result[label] = 0.0
                    elif base_value is None:
                        result[label] = compare_value
                    elif compare_value is None:
                        result[label] = -base_value
                    else:
                        result[label] = compare_value - base_value
            return result

    def table(self, item_names: Optional[Union[str, List[str]]] = None) -> Table:
        """
        Generate a table comparing values across all models for specific item(s).

        For each item, creates a label row followed by rows for each model showing
        values across all common years, separated by blank rows between items.

        Args:
            item_names (str, list, or None): Name of the item to compare, or list
                of item names. If None, all common items are included.

        Returns:
            Table: A formatted table with rows for each model showing values

        Raises:
            KeyError: If any item not found in all models
        """
        # Use all common items if none specified
        if item_names is None:
            item_names = self.common_items.copy()
        # Handle both single item and list of items
        elif isinstance(item_names, str):
            item_names = [item_names]

        # Validate all items exist in all models
        for name in item_names:
            if name not in self.common_items:
                raise KeyError(f"Item '{name}' not found in all models")

        model_row_pairs = []

        for i, item_name in enumerate(item_names):
            # Add blank row between items (except before the first item)
            if i > 0:
                blank_row = rt.BlankRow()
                model_row_pairs.append((self.models[0], blank_row))

            # Get item details from the first model
            item_label = self.models[0].line_item(item_name).label

            # Add label row for the item
            label_row = rt.LabelRow(label=item_label, bold=True)
            model_row_pairs.append((self.models[0], label_row))

            # Add a row for each model with its label and values
            for model, label in zip(self.models, self.labels):
                model_row = rt.ItemRow(name=item_name, label=label, bold=False)
                model_row_pairs.append((model, model_row))

        # Generate the table using the multi-model table generator
        table = generate_multi_model_table(model_row_pairs)

        return table

    def __repr__(self) -> str:
        """String representation of the comparison."""
        return (
            f"MultiModelCompare({len(self.models)} models, "
            f"{len(self.common_items)} common items, "
            f"{len(self.common_years)} common years)"
        )


def compare_models(
    models: List["Model"], labels: Optional[List[str]] = None
) -> Union["MultiModelCompare", "TwoModelCompare"]:
    """
    Create a comparison object for analyzing differences across models.

    Returns TwoModelCompare for exactly 2 models, or MultiModelCompare for 3+ models.

    Args:
        models (List[Model]): List of models to compare (at least 2 required)
        labels (List[str], optional): List of labels for each model.
            If None, uses "Model 1", "Model 2", etc. for MultiModelCompare,
            or "Base Model" and "Compare Model" for TwoModelCompare.

    Returns:
        TwoModelCompare: For exactly 2 models, a comparison object optimized for
            two-model comparisons
        MultiModelCompare: For 3+ models, a comparison object for multi-model analysis

    Raises:
        ValueError: If fewer than 2 models are provided
        ValueError: If labels are provided but don't match the number of models

    Example:
        >>> model1 = Model([...], years=[2020, 2021])
        >>> model2 = Model([...], years=[2020, 2021])
        >>> # Returns TwoModelCompare
        >>> comparison = compare_models([model1, model2], labels=["Base", "Scenario"])
        >>> diff = comparison.difference("revenue", 2020)
        >>>
        >>> # Returns MultiModelCompare
        >>> model3 = Model([...], years=[2020, 2021])
        >>> comparison = compare_models([model1, model2, model3])
        >>> table = comparison.table(["revenue", "expenses"])
    """
    from .two_model_compare import TwoModelCompare

    if len(models) == 2:
        # For exactly 2 models, use TwoModelCompare
        if labels is None:
            return TwoModelCompare(models[0], models[1])
        elif len(labels) != 2:
            raise ValueError(
                f"Number of labels ({len(labels)}) must match number of "
                f"models ({len(models)})"
            )
        else:
            # TwoModelCompare doesn't use labels in the same way, but we could
            # extend it to accept them in the future. For now, just ignore.
            return TwoModelCompare(models[0], models[1])
    else:
        # For 3+ models, use MultiModelCompare
        return MultiModelCompare(models, labels)
