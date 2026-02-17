"""
Tests for tags functionality in v2 API.
"""

import pytest

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class TestLineTags:
    """Tests for tags on line items."""

    def test_fixed_line_with_tags(self):
        """Test that FixedLine accepts and stores tags."""
        line = FixedLine(values={2024: 100}, tags=["income", "operational"])
        assert line.tags == ["income", "operational"]

    def test_fixed_line_without_tags(self):
        """Test that FixedLine defaults to empty list when no tags provided."""
        line = FixedLine(values={2024: 100})
        assert line.tags == []

    def test_formula_line_with_tags(self):
        """Test that FormulaLine accepts and stores tags."""
        line = FormulaLine(
            formula=lambda a, li, t: 100, tags=["expense", "operational"]
        )
        assert line.tags == ["expense", "operational"]

    def test_formula_line_without_tags(self):
        """Test that FormulaLine defaults to empty list when no tags provided."""
        line = FormulaLine(formula=lambda a, li, t: 100)
        assert line.tags == []


class TestLineItemResultTags:
    """Tests for accessing tags through LineItemResult."""

    def test_access_tags_through_result(self):
        """Test accessing tags through LineItemResult."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income", "operational"])
            expenses = FixedLine(values={2024: 60}, tags=["expense", "operational"])

        model = TestModel(periods=[2024])

        revenue_result = model["revenue"]
        assert revenue_result.tags == ["income", "operational"]

        expenses_result = model["expenses"]
        assert expenses_result.tags == ["expense", "operational"]

    def test_access_tags_empty_list(self):
        """Test accessing tags when line item has no tags."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        revenue_result = model["revenue"]
        assert revenue_result.tags == []


class TestTagNamespace:
    """Tests for li.tag namespace."""

    def test_sum_by_tag_single_item(self):
        """Test summing a single line item by tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])

        model = TestModel(periods=[2024, 2025])

        assert model.li.tag["income"][2024] == 100
        assert model.li.tag["income"][2025] == 110

    def test_sum_by_tag_multiple_items(self):
        """Test summing multiple line items by tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

        model = TestModel(periods=[2024, 2025])

        # Sum income items
        assert model.li.tag["income"][2024] == 105  # 100 + 5
        assert model.li.tag["income"][2025] == 116  # 110 + 6

        # Sum expense items
        assert model.li.tag["expense"][2024] == 60
        assert model.li.tag["expense"][2025] == 66

    def test_sum_by_tag_with_formula_lines(self):
        """Test summing line items that include FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])
            interest = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.05, tags=["income"]
            )
            expenses = FixedLine(values={2024: 60}, tags=["expense"])

        model = TestModel(periods=[2024])

        # Sum income items (fixed + formula)
        assert model.li.tag["income"][2024] == 105  # 100 + 5
        assert model.li.tag["expense"][2024] == 60

    def test_sum_by_tag_no_matching_items(self):
        """Test summing when no items have the tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])

        # No items with "expense" tag
        assert model.li.tag["expense"][2024] == 0

    def test_sum_by_tag_multiple_tags_per_item(self):
        """Test that items with multiple tags are counted in each tag sum."""

        class TestModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 100}, tags=["income", "operational", "recurring"]
            )
            interest = FixedLine(values={2024: 5}, tags=["income", "non-operational"])

        model = TestModel(periods=[2024])

        # Revenue appears in all its tags
        assert model.li.tag["income"][2024] == 105  # Both items
        assert model.li.tag["operational"][2024] == 100  # Only revenue
        assert model.li.tag["recurring"][2024] == 100  # Only revenue
        assert model.li.tag["non-operational"][2024] == 5  # Only interest

    def test_sum_by_tag_invalid_period(self):
        """Test that invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])

        with pytest.raises(KeyError, match="Period 2025 not found"):
            model.li.tag["income"][2025]

    def test_tags_in_formula(self):
        """Test using tags namespace in a formula."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

            # Calculate profit using tag sums
            profit = FormulaLine(
                formula=lambda a, li, t: li.tag["income"][t] - li.tag["expense"][t]
            )

        model = TestModel(periods=[2024, 2025])

        assert model.li.profit[2024] == 45  # 105 - 60
        assert model.li.profit[2025] == 50  # 116 - 66


class TestModelTags:
    """Tests for model.tags property."""

    def test_model_tags_multiple_tags(self):
        """Test getting all unique tags from model."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income", "operational"])
            interest = FixedLine(values={2024: 5}, tags=["income", "financial"])
            expenses = FixedLine(values={2024: 60}, tags=["expense", "operational"])

        model = TestModel(periods=[2024])

        tags = model.tags
        assert tags == ["expense", "financial", "income", "operational"]

    def test_model_tags_no_tags(self):
        """Test model with no tags returns empty list."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        model = TestModel(periods=[2024])

        assert model.tags == []

    def test_model_tags_duplicate_tags(self):
        """Test that duplicate tags are deduplicated."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income", "recurring"])
            interest = FixedLine(values={2024: 5}, tags=["income"])
            fees = FixedLine(values={2024: 2}, tags=["income", "recurring"])

        model = TestModel(periods=[2024])

        tags = model.tags
        # Should have 2 unique tags, sorted
        assert tags == ["income", "recurring"]

    def test_model_tags_single_tag(self):
        """Test model with single tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])

        assert model.tags == ["income"]

    def test_model_tags_mixed_line_types(self):
        """Test tags from both FixedLine and FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])
            expenses = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.6, tags=["expense"]
            )
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t],
                tags=["income", "calculated"],
            )

        model = TestModel(periods=[2024])

        tags = model.tags
        assert tags == ["calculated", "expense", "income"]


class TestModelTagSelection:
    """Tests for model.tag property to select line items by tag."""

    def test_tag_selection_single_tag(self):
        """Test selecting line items by a single tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])
            interest = FixedLine(values={2024: 5}, tags=["income"])
            expenses = FixedLine(values={2024: 60}, tags=["expense"])

        model = TestModel(periods=[2024])

        income_selection = model.tag["income"]
        assert income_selection.names == ["revenue", "interest"]

        expense_selection = model.tag["expense"]
        assert expense_selection.names == ["expenses"]

    def test_tag_selection_empty(self):
        """Test selecting line items with a tag that doesn't exist."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])

        # Tag doesn't exist
        selection = model.tag["expense"]
        assert selection.names == []

    def test_tag_selection_multiple_tags_per_item(self):
        """Test selecting when items have multiple tags."""

        class TestModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 100}, tags=["income", "operational", "recurring"]
            )
            interest = FixedLine(values={2024: 5}, tags=["income", "non-operational"])
            expenses = FixedLine(values={2024: 60}, tags=["expense", "operational"])

        model = TestModel(periods=[2024])

        # Items with "income" tag
        income_selection = model.tag["income"]
        assert set(income_selection.names) == {"revenue", "interest"}

        # Items with "operational" tag
        operational_selection = model.tag["operational"]
        assert set(operational_selection.names) == {"revenue", "expenses"}

    def test_tag_selection_preserves_order(self):
        """Test that tag selection preserves model order."""

        class TestModel(ProformaModel):
            expenses = FixedLine(values={2024: 60}, tags=["operational"])
            revenue = FixedLine(values={2024: 100}, tags=["operational"])
            interest = FixedLine(values={2024: 5}, tags=["operational"])

        model = TestModel(periods=[2024])

        selection = model.tag["operational"]
        # Should preserve order from model.line_item_names
        assert selection.names == ["expenses", "revenue", "interest"]

    def test_tag_selection_can_generate_table(self):
        """Test that tag selection can generate a table."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

        model = TestModel(periods=[2024, 2025])

        income_selection = model.tag["income"]
        table = income_selection.table()

        # Should have header + 2 items + blank + total (with include_total_row=True by default)
        assert len(table.cells) == 5

    def test_tag_selection_can_get_values(self):
        """Test that tag selection can get values for a period."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

        model = TestModel(periods=[2024, 2025])

        income_selection = model.tag["income"]
        values_2024 = income_selection.value(2024)

        assert values_2024 == {"revenue": 100, "interest": 5}

    def test_tag_selection_mixed_line_types(self):
        """Test tag selection with both FixedLine and FormulaLine."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])
            interest = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.05, tags=["income"]
            )
            expenses = FixedLine(values={2024: 60}, tags=["expense"])

        model = TestModel(periods=[2024])

        income_selection = model.tag["income"]
        assert set(income_selection.names) == {"revenue", "interest"}
