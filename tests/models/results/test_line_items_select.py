"""Tests for the new .select() API on LineItemsResults and Model."""

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


class TestLineItemsResultsSelectMethod:
    """Test the new .select() method on LineItemsResults."""

    def test_select_returns_line_items_results(self, sample_model):
        """Test that .select() returns a LineItemsResults instance."""
        result = sample_model.line_items.select(["revenue", "costs"])
        assert isinstance(result, LineItemsResults)

    def test_select_filters_items(self, sample_model):
        """Test that .select() filters to specified items."""
        result = sample_model.line_items.select(["revenue", "costs"])
        assert set(result.names) == {"revenue", "costs"}

    def test_select_single_item(self, sample_model):
        """Test selecting a single item."""
        result = sample_model.line_items.select(["revenue"])
        assert result.names == ["revenue"]

    def test_select_preserves_order(self, sample_model):
        """Test that .select() preserves the order of specified items."""
        result = sample_model.line_items.select(["profit", "revenue", "costs"])
        assert result.names == ["profit", "revenue", "costs"]

    def test_select_invalid_item_raises_error(self, sample_model):
        """Test that selecting an invalid item raises KeyError."""
        with pytest.raises(KeyError):
            sample_model.line_items.select(["invalid_item"])

    def test_select_empty_list_raises_error(self, sample_model):
        """Test that selecting an empty list raises ValueError."""
        with pytest.raises(ValueError):
            sample_model.line_items.select([])

    def test_select_chain_operations(self, sample_model):
        """Test that operations can be chained after .select()."""
        result = sample_model.line_items.select(["revenue", "costs"])
        # Should be able to call methods on the result
        total = result.total(2023)
        assert total == 1400  # 1000 + 400


class TestModelSelectMethod:
    """Test the new Model.select() convenience method."""

    def test_model_select_returns_line_items_results(self, sample_model):
        """Test that model.select() returns LineItemsResults."""
        result = sample_model.select(["revenue", "costs"])
        assert isinstance(result, LineItemsResults)

    def test_model_select_filters_items(self, sample_model):
        """Test that model.select() filters to specified items."""
        result = sample_model.select(["revenue", "costs"])
        assert set(result.names) == {"revenue", "costs"}

    def test_model_select_equivalent_to_line_items_select(self, sample_model):
        """Test that model.select() is equivalent to model.line_items.select()."""
        result1 = sample_model.select(["revenue", "costs"])
        result2 = sample_model.line_items.select(["revenue", "costs"])
        assert result1.names == result2.names

    def test_model_select_single_item(self, sample_model):
        """Test selecting a single item via model.select()."""
        result = sample_model.select(["profit"])
        assert result.names == ["profit"]


class TestBackwardsCompatibility:
    """Test that the new API doesn't break existing functionality."""

    def test_can_still_access_individual_line_item(self, sample_model):
        """Test that model.line_item() still works for accessing single items."""
        # The old API should still work
        result = sample_model.line_item("revenue")
        assert result.name == "revenue"

    def test_line_items_select_works_with_all_methods(self, sample_model):
        """Test that all LineItemsResults methods work with selected items."""
        selected = sample_model.line_items.select(["revenue", "costs"])
        
        # Test various methods
        assert len(selected.names) == 2
        assert selected.total(2023) == 1400
        table = selected.table()
        assert table is not None
        df = selected.to_dataframe()
        assert len(df) == 2
