"""
Tests for empty model initialization.

This module tests the ability to create an empty Model instance without
providing any line items or years.
"""

import pytest

from pyproforma.models.model.model import Model


class TestEmptyModelInitialization:
    """Test cases for initializing empty models."""

    def test_empty_model_initialization(self):
        """Test that Model() creates an empty model with empty years."""
        model = Model()

        # Check that model was created successfully
        assert model is not None
        assert isinstance(model, Model)

        # Check empty years (no default years for truly empty model)
        assert model.years == []

        # Check empty collections
        assert len(model._line_item_definitions) == 0
        assert len(model._category_definitions) == 0
        assert len(model.multi_line_items) == 0
        assert len(model.constraints) == 0

    def test_empty_model_with_custom_years(self):
        """Test empty model with custom years provided."""
        custom_years = [2020, 2021, 2022]
        model = Model(years=custom_years)

        assert model.years == custom_years
        assert len(model._line_item_definitions) == 0

    def test_empty_model_summary(self):
        """Test that summary works on empty model."""
        model = Model()
        summary = model.summary()

        assert summary["years_count"] == 0
        assert summary["line_items_count"] == 0
        assert summary["categories_count"] == 0
        assert summary["multi_line_items_count"] == 0
        assert summary["constraints_count"] == 0
        assert summary["defined_names_count"] == 0
        assert summary["line_items_by_category"] == {}
        assert summary["multi_line_item_names"] == []
        assert summary["constraint_names"] == []

    def test_empty_model_with_empty_lists(self):
        """Test providing empty lists explicitly."""
        model = Model(line_items=[], years=[2023, 2024])

        assert model.years == [2023, 2024]
        assert len(model._line_item_definitions) == 0

    def test_empty_model_properties(self):
        """Test that empty model properties work correctly."""
        model = Model()

        # Test property access
        assert model.line_item_names == []
        assert model.category_names == []
        assert model.line_item_names_by_category() == {}

    def test_empty_model_namespace_access(self):
        """Test that namespace properties are accessible on empty model."""
        model = Model()

        # These should not raise errors
        assert model.tables is not None
        assert model.charts is not None
        assert model.update is not None

    def test_empty_model_copy(self):
        """Test that empty model can be copied."""
        original = Model()
        copied = original.copy()

        assert copied is not original
        assert copied.years == original.years
        assert len(copied._line_item_definitions) == 0

    def test_empty_model_string_representation(self):
        """Test string representations work on empty model."""
        model = Model()

        # Should not raise errors
        str_repr = str(model._repr_html_())
        assert "Model Summary" in str_repr
        assert "Line Items: 0" in str_repr

    def test_model_with_line_items_but_no_years_now_allowed(self):
        """Test that providing line_items but no years now works (creates template)."""
        from pyproforma.models.line_item import LineItem

        line_item = LineItem(name="test", category="test_cat", formula="100")

        # This should now work - creates a model with empty years
        model = Model(line_items=[line_item])

        assert model.years == []
        assert len(model.line_item_names) == 2  # test + category total
        assert model.line_item_names[0] == "test"

        # Structural access should work
        assert model.line_item("test") is not None

        # But value access should fail since no years
        with pytest.raises(KeyError, match="Year .* not found in years"):
            model.value("test", 2023)

    def test_model_with_line_items_and_empty_years_now_allowed(self):
        """Test that providing line_items with empty years list now works."""
        from pyproforma.models.line_item import LineItem

        line_item = LineItem(name="test", category="test_cat", formula="100")

        # This should now work - creates a model with empty years
        model = Model(line_items=[line_item], years=[])

        assert model.years == []
        assert len(model.line_item_names) == 2  # test + category total
        assert model.line_item_names[0] == "test"

        # Test that we can add years later and make it functional
        model.years = [2023, 2024]
        model._recalculate()

        assert model.value("test", 2023) == 100.0
        assert model.value("test", 2024) == 100.0

    def test_normal_model_creation_still_works(self):
        """Test that normal model creation with line_items and years still works."""
        from pyproforma.models.line_item import LineItem

        line_item = LineItem(name="revenue", category="income", formula="1000")
        model = Model(line_items=[line_item], years=[2023, 2024])

        assert model.years == [2023, 2024]
        assert len(model._line_item_definitions) == 1
        assert model.value("revenue", 2023) == 1000
