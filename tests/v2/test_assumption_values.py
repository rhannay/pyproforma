"""
Tests for AssumptionValues class.
"""

import pytest

from pyproforma.v2.assumption_values import AssumptionValues


class TestAssumptionValues:
    """Tests for AssumptionValues class."""

    def test_initialization_empty(self):
        """Test creating an empty AssumptionValues."""
        av = AssumptionValues()
        assert av._values == {}

    def test_initialization_with_values(self):
        """Test creating AssumptionValues with initial values."""
        values = {"tax_rate": 0.21, "growth_rate": 0.1}
        av = AssumptionValues(values)
        assert av._values == values

    def test_get_existing_value(self):
        """Test getting an existing assumption value."""
        av = AssumptionValues({"tax_rate": 0.21})
        assert av.get("tax_rate") == 0.21

    def test_get_missing_value(self):
        """Test getting a missing assumption value."""
        av = AssumptionValues({"tax_rate": 0.21})
        assert av.get("missing") is None

    def test_get_with_default(self):
        """Test getting a missing value with default."""
        av = AssumptionValues({"tax_rate": 0.21})
        assert av.get("missing", 0.0) == 0.0

    def test_attribute_access(self):
        """Test accessing assumption values via attributes."""
        av = AssumptionValues({"tax_rate": 0.21, "growth_rate": 0.1})
        assert av.tax_rate == 0.21
        assert av.growth_rate == 0.1

    def test_attribute_access_missing(self):
        """Test that accessing missing attribute raises AttributeError."""
        av = AssumptionValues({"tax_rate": 0.21})
        with pytest.raises(AttributeError, match="Assumption 'missing' not found"):
            _ = av.missing

    def test_repr(self):
        """Test string representation."""
        av = AssumptionValues({"tax_rate": 0.21})
        assert "AssumptionValues" in repr(av)
        assert "tax_rate" in repr(av)
