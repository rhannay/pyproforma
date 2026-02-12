"""
Tests for LineItemValues class.
"""

import pytest

from pyproforma.v2.line_item_values import LineItemValue, LineItemValues


class TestLineItemValues:
    """Tests for LineItemValues class."""

    def test_initialization_empty(self):
        """Test creating an empty LineItemValues."""
        li = LineItemValues()
        assert li._values == {}
        assert li._periods == []

    def test_initialization_with_values(self):
        """Test creating LineItemValues with initial values."""
        values = {"revenue": {2024: 100, 2025: 110}}
        periods = [2024, 2025]
        li = LineItemValues(values, periods)
        assert li._values == values
        assert li._periods == periods

    def test_get_all_periods(self):
        """Test getting all period values for a line item."""
        values = {"revenue": {2024: 100, 2025: 110}}
        li = LineItemValues(values)
        assert li.get("revenue") == {2024: 100, 2025: 110}

    def test_get_specific_period(self):
        """Test getting a specific period value."""
        values = {"revenue": {2024: 100, 2025: 110}}
        li = LineItemValues(values)
        assert li.get("revenue", 2024) == 100
        assert li.get("revenue", 2025) == 110

    def test_get_missing_line_item(self):
        """Test getting a missing line item."""
        li = LineItemValues({"revenue": {2024: 100}})
        assert li.get("missing") is None
        assert li.get("missing", 2024) is None

    def test_get_missing_period(self):
        """Test getting a missing period for an existing line item."""
        li = LineItemValues({"revenue": {2024: 100}})
        assert li.get("revenue", 2025) is None

    def test_set_value(self):
        """Test setting a value for a line item."""
        li = LineItemValues()
        li.set("revenue", 2024, 100)
        assert li.get("revenue", 2024) == 100

    def test_set_value_existing_line_item(self):
        """Test setting a value for an existing line item."""
        li = LineItemValues({"revenue": {2024: 100}})
        li.set("revenue", 2025, 110)
        assert li.get("revenue", 2024) == 100
        assert li.get("revenue", 2025) == 110

    def test_attribute_access(self):
        """Test accessing line item values via attributes."""
        values = {"revenue": {2024: 100, 2025: 110}}
        li = LineItemValues(values)
        # Now returns a LineItemValue object that supports subscripting
        revenue_item = li.revenue
        assert isinstance(revenue_item, LineItemValue)
        assert revenue_item[2024] == 100
        assert revenue_item[2025] == 110

    def test_attribute_access_missing(self):
        """Test that accessing missing attribute raises AttributeError."""
        li = LineItemValues({"revenue": {2024: 100}})
        with pytest.raises(AttributeError, match="Line item 'missing' not found"):
            _ = li.missing

    def test_repr(self):
        """Test string representation."""
        li = LineItemValues({"revenue": {2024: 100}})
        assert "LineItemValues" in repr(li)


class TestLineItemValue:
    """Tests for LineItemValue class."""

    def test_initialization(self):
        """Test creating a LineItemValue."""
        values = {2024: 100, 2025: 110}
        item = LineItemValue("revenue", values)
        assert item._name == "revenue"
        assert item._values == values

    def test_get_existing_period(self):
        """Test getting an existing period value."""
        item = LineItemValue("revenue", {2024: 100, 2025: 110})
        assert item.get(2024) == 100
        assert item.get(2025) == 110

    def test_get_missing_period(self):
        """Test getting a missing period value."""
        item = LineItemValue("revenue", {2024: 100})
        assert item.get(2025) is None

    def test_get_with_default(self):
        """Test getting a missing period with default."""
        item = LineItemValue("revenue", {2024: 100})
        assert item.get(2025, 0) == 0

    def test_subscript_access(self):
        """Test accessing values via subscript notation."""
        item = LineItemValue("revenue", {2024: 100, 2025: 110})
        assert item[2024] == 100
        assert item[2025] == 110

    def test_subscript_access_missing(self):
        """Test that accessing missing period raises KeyError."""
        item = LineItemValue("revenue", {2024: 100})
        with pytest.raises(KeyError, match="Period 2025 not found"):
            _ = item[2025]

    def test_repr(self):
        """Test string representation."""
        item = LineItemValue("revenue", {2024: 100})
        assert "LineItemValue" in repr(item)
        assert "revenue" in repr(item)
