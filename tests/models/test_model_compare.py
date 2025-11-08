"""
Unit tests for Model.compare() method with support for both single model
and list of models.
"""

import pytest

from pyproforma import LineItem, Model, MultiModelCompare, TwoModelCompare


class TestModelCompareSingleModel:
    """Test Model.compare() with a single other model."""

    def test_compare_returns_two_model_compare(self):
        """Test that comparing with a single model returns TwoModelCompare."""
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

        comparison = model1.compare(model2)

        assert isinstance(comparison, TwoModelCompare)
        assert comparison.base_model == model1
        assert comparison.compare_model == model2

    def test_compare_difference_method_works(self):
        """Test that TwoModelCompare methods work correctly."""
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

        comparison = model1.compare(model2)
        diff = comparison.difference("revenue", 2020)

        assert diff == 20.0  # 120 - 100


class TestModelCompareMultipleModels:
    """Test Model.compare() with a list of other models."""

    def test_compare_with_list_returns_multi_model_compare(self):
        """Test that comparing with a list returns MultiModelCompare."""
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

        comparison = model1.compare([model2, model3])

        assert isinstance(comparison, MultiModelCompare)
        assert len(comparison.models) == 3
        assert comparison.models[0] == model1
        assert comparison.models[1] == model2
        assert comparison.models[2] == model3

    def test_compare_with_list_difference_uses_first_as_baseline(self):
        """Test that MultiModelCompare uses first model as baseline."""
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

        comparison = model1.compare([model2, model3])
        diff = comparison.difference("revenue", 2020)

        # First model (model1) is baseline, so its difference is 0
        assert diff["Model 1"] == 0.0
        assert diff["Model 2"] == 20.0  # 120 - 100
        assert diff["Model 3"] == 10.0  # 110 - 100

    def test_compare_with_empty_list_raises_error(self):
        """Test that comparing with an empty list raises an error."""
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

        # Passing an empty list means only 1 model total (model1)
        with pytest.raises(ValueError, match="At least 2 models are required"):
            model1.compare([])

    def test_compare_with_single_item_list_returns_multi_model_compare(self):
        """
        Test that comparing with a list of 1 model still returns
        MultiModelCompare.
        """
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

        # List with 1 model means 2 total, should still use MultiModelCompare
        comparison = model1.compare([model2])

        assert isinstance(comparison, MultiModelCompare)
        assert len(comparison.models) == 2


class TestModelCompareBackwardCompatibility:
    """Test that Model.compare() maintains backward compatibility."""

    def test_compare_with_single_model_positional_arg(self):
        """Test that old usage pattern still works."""
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

        # Old usage pattern should still work
        comparison = model1.compare(model2)

        assert isinstance(comparison, TwoModelCompare)
        assert comparison.difference("revenue", 2020) == 20.0
