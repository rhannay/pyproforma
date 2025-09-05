"""Tests for table_generator module."""

import pytest

from pyproforma import LineItem, Model
from pyproforma.tables.row_types import ItemRow
from pyproforma.tables.table_generator import (
    TableGenerationError,
    generate_multi_model_table,
    generate_table_from_template,
)


class TestTableGenerationWithEmptyYears:
    """Test table generation behavior when model has empty years."""

    def test_generate_table_from_template_with_empty_years_raises_error(self):
        """Test that generating table with empty years raises TableGenerationError."""
        # Create empty model
        model = Model()
        template = [ItemRow(name="revenue")]

        with pytest.raises(TableGenerationError, match="model has no years defined"):
            generate_table_from_template(model, template)

    def test_generate_table_from_template_with_line_items_but_empty_years_raises_error(
        self,
    ):
        """Test that model with line items but empty years raises error."""
        line_item = LineItem(name="revenue", category="income", formula="1000")
        model = Model(line_items=[line_item], years=[])
        template = [ItemRow(name="revenue")]

        with pytest.raises(TableGenerationError, match="model has no years defined"):
            generate_table_from_template(model, template)

    def test_generate_table_from_template_with_years_works_normally(self):
        """Test that model with years generates table normally."""
        line_item = LineItem(name="revenue", category="income", formula="1000")
        model = Model(line_items=[line_item], years=[2023, 2024])
        template = [ItemRow(name="revenue")]

        # Should not raise an error
        table = generate_table_from_template(model, template)
        assert table is not None
        assert len(table.columns) == 3  # Year + 2 years
        assert len(table.rows) == 1

    def test_generate_multi_model_table_with_empty_models_raises_error(self):
        """Test that multi-model table with all empty years raises error."""
        model1 = Model()
        model2 = Model()

        model_row_pairs = [
            (model1, ItemRow(name="revenue")),
            (model2, ItemRow(name="expenses")),
        ]

        with pytest.raises(TableGenerationError, match="all models have empty years"):
            generate_multi_model_table(model_row_pairs)

    def test_generate_multi_model_table_with_no_models_raises_error(self):
        """Test that multi-model table with no models raises error."""
        with pytest.raises(TableGenerationError, match="no models provided"):
            generate_multi_model_table([])

    def test_generate_multi_model_table_with_at_least_one_model_with_years_works(self):
        """Test that multi-model table works when at least one model has years."""
        line_item1 = LineItem(name="revenue", category="income", formula="1000")
        model1 = Model(line_items=[line_item1], years=[2023, 2024])

        model_row_pairs = [
            (model1, ItemRow(name="revenue")),
        ]

        # Should work because model1 has years
        table = generate_multi_model_table(model_row_pairs)
        assert table is not None
        assert len(table.columns) == 3  # Year + 2 years from model1
        assert len(table.rows) == 1  # Only one row from model1


class TestTableGenerationErrorMessages:
    """Test that error messages are descriptive and helpful."""

    def test_empty_years_error_message_is_descriptive(self):
        """Test that error message explains the problem and solution."""
        model = Model()
        template = [ItemRow(name="revenue")]

        with pytest.raises(TableGenerationError) as exc_info:
            generate_table_from_template(model, template)

        error_message = str(exc_info.value)
        assert "model has no years defined" in error_message
        assert "Please add years to the model" in error_message
        assert "before generating tables" in error_message

    def test_multi_model_empty_years_error_message_is_descriptive(self):
        """Test that multi-model error message is descriptive."""
        model1 = Model()
        model2 = Model()

        model_row_pairs = [
            (model1, ItemRow(name="revenue")),
            (model2, ItemRow(name="expenses")),
        ]

        with pytest.raises(TableGenerationError) as exc_info:
            generate_multi_model_table(model_row_pairs)

        error_message = str(exc_info.value)
        assert "all models have empty years" in error_message
        assert "Please add years to at least one model" in error_message

    def test_no_models_error_message_is_descriptive(self):
        """Test that no models error message is descriptive."""
        with pytest.raises(TableGenerationError) as exc_info:
            generate_multi_model_table([])

        error_message = str(exc_info.value)
        assert "no models provided" in error_message
