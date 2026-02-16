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


class TestTagsNamespace:
    """Tests for li.tags namespace."""

    def test_sum_by_tag_single_item(self):
        """Test summing a single line item by tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])

        model = TestModel(periods=[2024, 2025])
        
        assert model.li.tags["income"][2024] == 100
        assert model.li.tags["income"][2025] == 110

    def test_sum_by_tag_multiple_items(self):
        """Test summing multiple line items by tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

        model = TestModel(periods=[2024, 2025])
        
        # Sum income items
        assert model.li.tags["income"][2024] == 105  # 100 + 5
        assert model.li.tags["income"][2025] == 116  # 110 + 6
        
        # Sum expense items
        assert model.li.tags["expense"][2024] == 60
        assert model.li.tags["expense"][2025] == 66

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
        assert model.li.tags["income"][2024] == 105  # 100 + 5
        assert model.li.tags["expense"][2024] == 60

    def test_sum_by_tag_no_matching_items(self):
        """Test summing when no items have the tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])
        
        # No items with "expense" tag
        assert model.li.tags["expense"][2024] == 0

    def test_sum_by_tag_multiple_tags_per_item(self):
        """Test that items with multiple tags are counted in each tag sum."""

        class TestModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 100}, tags=["income", "operational", "recurring"]
            )
            interest = FixedLine(values={2024: 5}, tags=["income", "non-operational"])

        model = TestModel(periods=[2024])
        
        # Revenue appears in all its tags
        assert model.li.tags["income"][2024] == 105  # Both items
        assert model.li.tags["operational"][2024] == 100  # Only revenue
        assert model.li.tags["recurring"][2024] == 100  # Only revenue
        assert model.li.tags["non-operational"][2024] == 5  # Only interest

    def test_sum_by_tag_invalid_period(self):
        """Test that invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, tags=["income"])

        model = TestModel(periods=[2024])
        
        with pytest.raises(KeyError, match="Period 2025 not found"):
            model.li.tags["income"][2025]

    def test_tags_in_formula(self):
        """Test using tags namespace in a formula."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])
            
            # Calculate profit using tag sums
            profit = FormulaLine(
                formula=lambda a, li, t: li.tags["income"][t] - li.tags["expense"][t]
            )

        model = TestModel(periods=[2024, 2025])
        
        assert model.li.profit[2024] == 45  # 105 - 60
        assert model.li.profit[2025] == 50  # 116 - 66
