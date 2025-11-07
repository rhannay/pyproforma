"""
Unit tests for MultiModelCompare class and compare_models function.
"""

import pytest

from pyproforma import LineItem, Model, compare_models
from pyproforma.models.multi_model_compare import MultiModelCompare


class TestMultiModelCompareInit:
    """Test initialization of MultiModelCompare."""

    def test_init_with_two_models(self):
        """Test initialization with two models and no labels."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])

        assert len(comparison.models) == 2
        assert comparison.labels == ["Model 1", "Model 2"]
        assert comparison.common_years == [2020, 2021]
        assert comparison.common_items == ["revenue"]

    def test_init_with_three_models_custom_labels(self):
        """Test initialization with three models and custom labels."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )
        model3 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 110, 2021: 155},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare(
            [model1, model2, model3], labels=["Base", "Optimistic", "Pessimistic"]
        )

        assert len(comparison.models) == 3
        assert comparison.labels == ["Base", "Optimistic", "Pessimistic"]
        assert comparison.common_years == [2020, 2021]

    def test_init_with_less_than_two_models_raises_error(self):
        """Test that initialization with fewer than 2 models raises ValueError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )

        with pytest.raises(ValueError, match="At least 2 models are required"):
            MultiModelCompare([model1])

    def test_init_with_mismatched_labels_raises_error(self):
        """Test that providing wrong number of labels raises ValueError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        with pytest.raises(
            ValueError, match="Number of labels .* must match number of models"
        ):
            MultiModelCompare([model1, model2], labels=["Only One Label"])

    def test_init_with_no_overlapping_years_raises_error(self):
        """Test that models with no common years raise ValueError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2021: 120},
                )
            ],
            years=[2021],
        )

        with pytest.raises(
            ValueError, match="Models must have at least one overlapping year"
        ):
            MultiModelCompare([model1, model2])

    def test_init_with_model_without_years_raises_error(self):
        """Test that a model without years raises ValueError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={},
                )
            ],
            years=[],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        with pytest.raises(ValueError, match="has no years defined"):
            MultiModelCompare([model1, model2])


class TestMultiModelCompareValidation:
    """Test validation logic in MultiModelCompare."""

    def test_common_items_identified_correctly(self):
        """Test that common items are identified correctly."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                ),
                LineItem(
                    name="expenses",
                    label="Expenses",
                    category="costs",
                    values={2020: 50},
                ),
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                ),
                LineItem(
                    name="profit",
                    label="Profit",
                    category="income",
                    values={2020: 70},
                ),
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2])

        assert comparison.common_items == ["revenue"]
        assert len(comparison.unique_items) == 2
        assert "expenses" in comparison.unique_items[0]
        assert "profit" in comparison.unique_items[1]

    def test_common_years_across_multiple_models(self):
        """Test that common years are correctly identified across multiple models."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 110, 2022: 120},
                )
            ],
            years=[2020, 2021, 2022],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2021: 115, 2022: 125, 2023: 130},
                )
            ],
            years=[2021, 2022, 2023],
        )
        model3 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 105, 2021: 112, 2022: 122},
                )
            ],
            years=[2020, 2021, 2022],
        )

        comparison = MultiModelCompare([model1, model2, model3])

        assert comparison.common_years == [2021, 2022]


class TestMultiModelCompareDifference:
    """Test difference method of MultiModelCompare."""

    def test_difference_for_specific_year(self):
        """Test calculating differences for a specific year."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )
        model3 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 110, 2021: 155},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2, model3])
        diff = comparison.difference("revenue", 2020)

        assert diff["Model 1"] == 0.0  # Baseline
        assert diff["Model 2"] == 20.0  # 120 - 100
        assert diff["Model 3"] == 10.0  # 110 - 100

    def test_difference_for_all_years(self):
        """Test calculating differences for all common years."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])
        diff = comparison.difference("revenue")

        assert diff["Model 1"][2020] == 0.0
        assert diff["Model 1"][2021] == 0.0
        assert diff["Model 2"][2020] == 20.0
        assert diff["Model 2"][2021] == 10.0

    def test_difference_with_none_values(self):
        """Test difference calculation handles None values correctly."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: None, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: None},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])
        diff = comparison.difference("revenue")

        assert diff["Model 1"][2020] == 0.0
        assert diff["Model 2"][2020] == 120  # None -> 120 = 120
        assert diff["Model 2"][2021] == -150  # 150 -> None = -150

    def test_difference_with_nonexistent_item_raises_error(self):
        """Test that requesting difference for nonexistent item raises KeyError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2])

        with pytest.raises(KeyError, match="not found in all models"):
            comparison.difference("nonexistent")

    def test_difference_with_nonexistent_year_raises_error(self):
        """Test that requesting difference for nonexistent year raises KeyError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2])

        with pytest.raises(KeyError, match="not found in all models"):
            comparison.difference("revenue", 2021)

    def test_difference_with_custom_labels(self):
        """Test that difference uses custom labels correctly."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2], labels=["Base", "Scenario"])
        diff = comparison.difference("revenue", 2020)

        assert "Base" in diff
        assert "Scenario" in diff
        assert diff["Base"] == 0.0
        assert diff["Scenario"] == 20.0


class TestMultiModelCompareDifferenceTable:
    """Test difference_table method of MultiModelCompare."""

    def test_difference_table_single_item(self):
        """Test generating a difference table for a single item."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])
        table = comparison.difference_table("revenue")

        # Table should have columns and rows
        assert table.columns is not None
        assert table.rows is not None
        assert len(table.rows) > 0

    def test_difference_table_multiple_items(self):
        """Test generating a difference table for multiple items."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                ),
                LineItem(
                    name="expenses",
                    label="Expenses",
                    category="costs",
                    values={2020: 50, 2021: 60},
                ),
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                ),
                LineItem(
                    name="expenses",
                    label="Expenses",
                    category="costs",
                    values={2020: 55, 2021: 65},
                ),
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])
        table = comparison.difference_table(["revenue", "expenses"])

        # Table should have rows for both items plus labels and blank rows
        # At least: label1, model1, model2, blank, label2, model1, model2
        assert len(table.rows) > 4

    def test_difference_table_with_nonexistent_item_raises_error(self):
        """Test that requesting table for nonexistent item raises KeyError."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2])

        with pytest.raises(KeyError, match="not found in all models"):
            comparison.difference_table("nonexistent")

    def test_difference_table_with_three_models(self):
        """Test generating a table with three models."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )
        model3 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 110},
                )
            ],
            years=[2020],
        )

        comparison = MultiModelCompare([model1, model2, model3])
        table = comparison.difference_table("revenue")

        # Should have rows for label + 3 models
        assert len(table.rows) >= 4


class TestCompareModelsFunction:
    """Test the compare_models function."""

    def test_compare_models_returns_multi_model_compare(self):
        """Test that compare_models returns a MultiModelCompare instance."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = compare_models([model1, model2])

        assert isinstance(comparison, MultiModelCompare)
        assert len(comparison.models) == 2

    def test_compare_models_with_labels(self):
        """Test compare_models function with custom labels."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = compare_models([model1, model2], labels=["Base", "Optimistic"])

        assert comparison.labels == ["Base", "Optimistic"]

    def test_compare_models_accessible_from_main_package(self):
        """Test that compare_models is accessible from main pyproforma package."""
        from pyproforma import compare_models as cm

        assert cm is not None
        assert callable(cm)


class TestMultiModelCompareRepr:
    """Test __repr__ method of MultiModelCompare."""

    def test_repr_output(self):
        """Test that __repr__ returns expected format."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )

        comparison = MultiModelCompare([model1, model2])
        repr_str = repr(comparison)

        assert "MultiModelCompare" in repr_str
        assert "2 models" in repr_str
        assert "1 common items" in repr_str
        assert "2 common years" in repr_str
