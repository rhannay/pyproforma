"""Tests for the indexing API on LineItemsResults."""

import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.results import LineItemsResults


@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    line_items = [
        LineItem(name="revenue", category="income", values={2023: 1000, 2024: 1100}),
        LineItem(name="costs", category="expenses", values={2023: 400, 2024: 450}),
        LineItem(name="salaries", category="expenses", values={2023: 300, 2024: 320}),
        LineItem(name="profit", category="income", formula="revenue - costs - salaries"),
    ]
    return Model(line_items=line_items, years=[2023, 2024])


class TestLineItemsAsProperty:
    """Test that Model.line_items works as a property."""

    def test_line_items_property_returns_line_items_results(self, sample_model):
        """Test that model.line_items returns LineItemsResults."""
        result = sample_model.line_items
        assert isinstance(result, LineItemsResults)

    def test_line_items_property_returns_all_items(self, sample_model):
        """Test that model.line_items returns all line items."""
        result = sample_model.line_items
        assert set(result.names) == {"revenue", "costs", "salaries", "profit"}

    def test_line_items_property_no_parentheses(self, sample_model):
        """Test that model.line_items works without parentheses."""
        # Should work as a property
        result = sample_model.line_items
        assert len(result.names) == 4


class TestLineItemsResultsIndexing:
    """Test the indexing on LineItemsResults."""

    def test_indexing_returns_line_items_results(self, sample_model):
        """Test that indexing returns a LineItemsResults instance."""
        result = sample_model.line_items[["revenue", "costs"]]
        assert isinstance(result, LineItemsResults)

    def test_indexing_filters_items(self, sample_model):
        """Test that indexing filters to specified items."""
        result = sample_model.line_items[["revenue", "costs"]]
        assert set(result.names) == {"revenue", "costs"}

    def test_indexing_single_item(self, sample_model):
        """Test indexing with a single item."""
        result = sample_model.line_items[["revenue"]]
        assert result.names == ["revenue"]

    def test_indexing_preserves_order(self, sample_model):
        """Test that indexing preserves the order of specified items."""
        result = sample_model.line_items[["profit", "revenue", "costs"]]
        assert result.names == ["profit", "revenue", "costs"]

    def test_indexing_invalid_item_raises_error(self, sample_model):
        """Test that indexing with an invalid item raises KeyError."""
        with pytest.raises(KeyError):
            sample_model.line_items[["invalid_item"]]

    def test_indexing_empty_list_raises_error(self, sample_model):
        """Test that indexing with an empty list raises ValueError."""
        with pytest.raises(ValueError):
            sample_model.line_items[[]]

    def test_indexing_non_list_raises_error(self, sample_model):
        """Test that indexing with a non-list raises ValueError."""
        with pytest.raises(ValueError):
            sample_model.line_items["revenue"]

    def test_indexing_chain_operations(self, sample_model):
        """Test that operations can be chained after indexing."""
        result = sample_model.line_items[["revenue", "costs"]]
        # Should be able to call methods on the result
        total = result.total(2023)
        assert total == 1400  # 1000 + 400

    def test_indexing_nested(self, sample_model):
        """Test that indexing can be nested."""
        # First get a subset
        subset = sample_model.line_items[["revenue", "costs", "salaries"]]
        # Then get a subset of the subset
        nested = subset[["revenue", "costs"]]
        assert set(nested.names) == {"revenue", "costs"}


class TestBackwardsCompatibility:
    """Test that the new API doesn't break existing functionality."""

    def test_can_still_access_individual_line_item(self, sample_model):
        """Test that model.line_item() still works for accessing single items."""
        # The old API should still work
        result = sample_model.line_item("revenue")
        assert result.name == "revenue"

    def test_line_items_indexing_works_with_all_methods(self, sample_model):
        """Test that all LineItemsResults methods work with indexed items."""
        selected = sample_model.line_items[["revenue", "costs"]]
        
        # Test various methods
        assert len(selected.names) == 2
        assert selected.total(2023) == 1400
        table = selected.table()
        assert table is not None
        df = selected.to_dataframe()
        assert len(df) == 2
