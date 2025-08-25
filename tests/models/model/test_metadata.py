"""
Tests for metadata collection utilities.

This module tests the metadata collection functions for categories and line items,
including their integration with multi-line items.
"""

import pytest

from pyproforma import Category, LineItem
from pyproforma.models.model.metadata import (
    collect_category_metadata,
    collect_line_item_metadata,
)
from pyproforma.models.multi_line_item.debt import Debt


class TestCollectCategoryMetadata:
    """Test the collect_category_metadata function."""

    def test_empty_categories_and_multi_line_items(self):
        """Test with empty input lists."""
        result = collect_category_metadata([], [])
        assert result == []

        result = collect_category_metadata([])
        assert result == []

    def test_single_category_without_total(self):
        """Test with a single category that doesn't include totals."""
        categories = [Category(name="revenue", label="Revenue", include_total=False)]
        result = collect_category_metadata(categories)

        expected = [{
            'name': 'revenue',
            'label': 'Revenue',
            'include_total': False,
            'total_name': None,
            'total_label': None,
            'system_generated': False
        }]
        assert result == expected

    def test_single_category_with_total(self):
        """Test with a single category that includes totals."""
        categories = [Category(
            name="expenses",
            label="Expenses",
            include_total=True,
            total_label="Total Expenses"
        )]
        result = collect_category_metadata(categories)

        expected = [
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': True,
                'total_name': 'total_expenses',
                'total_label': 'Total Expenses',
                'system_generated': False
            },
            {
                'name': 'category_totals',
                'label': 'Category Totals',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': True
            }
        ]
        assert result == expected

    def test_multiple_categories_mixed_totals(self):
        """Test with multiple categories, some with totals."""
        categories = [
            Category(name="revenue", label="Revenue", include_total=False),
            Category(
                name="expenses",
                label="Expenses",
                include_total=True,
                total_label="Total Expenses"
            ),
            Category(
                name="assets",
                label="Assets",
                include_total=True,
                total_label="Total Assets"
            )
        ]
        result = collect_category_metadata(categories)

        expected = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': False
            },
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': True,
                'total_name': 'total_expenses',
                'total_label': 'Total Expenses',
                'system_generated': False
            },
            {
                'name': 'assets',
                'label': 'Assets',
                'include_total': True,
                'total_name': 'total_assets',
                'total_label': 'Total Assets',
                'system_generated': False
            },
            {
                'name': 'category_totals',
                'label': 'Category Totals',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': True
            }
        ]
        assert result == expected

    def test_with_multi_line_items(self):
        """Test with multi-line items included."""
        categories = [Category(name="revenue", label="Revenue", include_total=False)]
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = collect_category_metadata(categories, multi_line_items)

        expected = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': False
            },
            {
                'name': 'debt',
                'label': 'debt (Multi-Line Item)',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': True
            }
        ]
        assert result == expected

    def test_duplicate_multi_line_item_name_ignored(self):
        """Test that multi-line items with existing category names are ignored."""
        categories = [Category(name="debt", label="Debt Category", include_total=False)]
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = collect_category_metadata(categories, multi_line_items)

        # Should only have the original category, not the multi-line item
        expected = [{
            'name': 'debt',
            'label': 'Debt Category',
            'include_total': False,
            'total_name': None,
            'total_label': None,
            'system_generated': False
        }]
        assert result == expected

    def test_multiple_multi_line_items(self):
        """Test with multiple multi-line items."""
        categories = []
        debt1 = Debt(name="debt1", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        debt2 = Debt(name="debt2", par_amount={2020: 2000}, interest_rate=0.06, term=25)
        multi_line_items = [debt1, debt2]

        result = collect_category_metadata(categories, multi_line_items)

        expected = [
            {
                'name': 'debt1',
                'label': 'debt1 (Multi-Line Item)',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': True
            },
            {
                'name': 'debt2',
                'label': 'debt2 (Multi-Line Item)',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': True
            }
        ]
        assert result == expected


class TestCollectLineItemMetadata:
    """Test the collect_line_item_metadata function."""

    def test_empty_inputs(self):
        """Test with empty input lists."""
        result = collect_line_item_metadata([], [], [])
        assert result == []

    def test_single_line_item(self):
        """Test with a single line item."""
        line_items = [LineItem(
            name="revenue",
            label="Revenue",
            category="income",
            values={2020: 1000},
            value_format="no_decimals"
        )]
        category_metadata = []
        multi_line_items = []

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        expected = [{
            'name': 'revenue',
            'label': 'Revenue',
            'value_format': 'no_decimals',
            'source_type': 'line_item',
            'source_name': 'revenue',
            'category': 'income'
        }]
        assert result == expected

    def test_multiple_line_items_different_formats(self):
        """Test with multiple line items with different value formats."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2020: 1000},
                value_format="no_decimals"
            ),
            LineItem(
                name="growth_rate",
                label="Growth Rate",
                category="assumptions",
                values={2020: 0.05},
                value_format="percent"
            ),
            LineItem(
                name="description",
                label="Description",
                category="notes",
                values={2020: "test"},
                value_format="str"
            )
        ]
        category_metadata = []
        multi_line_items = []

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        expected = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'value_format': 'no_decimals',
                'source_type': 'line_item',
                'source_name': 'revenue',
                'category': 'income'
            },
            {
                'name': 'growth_rate',
                'label': 'Growth Rate',
                'value_format': 'percent',
                'source_type': 'line_item',
                'source_name': 'growth_rate',
                'category': 'assumptions'
            },
            {
                'name': 'description',
                'label': 'Description',
                'value_format': 'str',
                'source_type': 'line_item',
                'source_name': 'description',
                'category': 'notes'
            }
        ]
        assert result == expected

    def test_category_totals_included(self):
        """Test that category totals are included when categories have items."""
        line_items = [
            LineItem(name="rev1", label="Revenue 1", category="revenue", values={2020: 1000}),
            LineItem(name="rev2", label="Revenue 2", category="revenue", values={2020: 2000}),
            LineItem(name="exp1", label="Expense 1", category="expenses", values={2020: 500})
        ]
        category_metadata = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'include_total': True,
                'total_name': 'total_revenue',
                'total_label': 'Total Revenue',
                'system_generated': False
            },
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': True,
                'total_name': 'total_expenses',
                'total_label': 'Total Expenses',
                'system_generated': False
            }
        ]
        multi_line_items = []

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        # Should include line items and category totals
        assert len(result) == 5  # 3 line items + 2 category totals

        # Check that category totals are included
        total_revenue = next(item for item in result if item['name'] == 'total_revenue')
        assert total_revenue == {
            'name': 'total_revenue',
            'label': 'Total Revenue',
            'value_format': 'no_decimals',
            'source_type': 'category',
            'source_name': 'revenue',
            'category': 'category_totals'
        }

    def test_category_totals_excluded_if_no_items(self):
        """Test that category totals are excluded when categories have no items."""
        line_items = [
            LineItem(name="rev1", label="Revenue 1", category="revenue", values={2020: 1000})
        ]
        category_metadata = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'include_total': True,
                'total_name': 'total_revenue',
                'total_label': 'Total Revenue',
                'system_generated': False
            },
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': True,
                'total_name': 'total_expenses',
                'total_label': 'Total Expenses',
                'system_generated': False
            }
        ]
        multi_line_items = []

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        # Should include line item and only revenue total (expenses has no items)
        assert len(result) == 2
        names = [item['name'] for item in result]
        assert 'rev1' in names
        assert 'total_revenue' in names
        assert 'total_expenses' not in names

    def test_multi_line_items_included(self):
        """Test that multi-line items are included in metadata."""
        line_items = []
        category_metadata = []
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        # Should include all defined names from the debt multi-line item
        debt_names = debt.defined_names
        assert len(result) == len(debt_names)

        for debt_name in debt_names:
            matching_item = next(item for item in result if item['name'] == debt_name)
            assert matching_item == {
                'name': debt_name,
                'label': debt_name,
                'value_format': 'no_decimals',
                'source_type': 'multi_line_item',
                'source_name': 'debt',
                'category': 'debt'
            }

    def test_duplicate_names_raise_error(self):
        """Test that duplicate names raise a ValueError."""
        line_items = [
            LineItem(name="revenue", label="Revenue", category="income", values={2020: 1000})
        ]
        category_metadata = [
            {
                'name': 'income',
                'label': 'Income',
                'include_total': True,
                'total_name': 'revenue',  # Duplicate name!
                'total_label': 'Total Income',
                'system_generated': False
            }
        ]
        multi_line_items = []

        with pytest.raises(ValueError) as exc_info:
            collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        assert "Duplicate defined names found in Model: revenue" in str(exc_info.value)

    def test_multiple_duplicate_names_raise_error(self):
        """Test that multiple duplicate names are all reported in the error."""
        line_items = [
            LineItem(name="revenue", label="Revenue", category="income", values={2020: 1000}),
            LineItem(name="cost", label="Cost", category="expenses", values={2020: 500})
        ]
        category_metadata = [
            {
                'name': 'income',
                'label': 'Income',
                'include_total': True,
                'total_name': 'revenue',  # Duplicate name!
                'total_label': 'Total Income',
                'system_generated': False
            },
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': True,
                'total_name': 'cost',  # Another duplicate name!
                'total_label': 'Total Expenses',
                'system_generated': False
            }
        ]
        multi_line_items = []

        with pytest.raises(ValueError) as exc_info:
            collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        error_msg = str(exc_info.value)
        assert "Duplicate defined names found in Model:" in error_msg
        assert "revenue" in error_msg
        assert "cost" in error_msg

    def test_comprehensive_integration(self):
        """Test with a comprehensive mix of all component types."""
        # Line items
        line_items = [
            LineItem(name="rev1", label="Revenue 1", category="revenue", values={2020: 1000}),
            LineItem(name="exp1", label="Expense 1", category="expenses", values={2020: 500})
        ]

        # Category metadata with totals
        category_metadata = [
            {
                'name': 'revenue',
                'label': 'Revenue',
                'include_total': True,
                'total_name': 'total_revenue',
                'total_label': 'Total Revenue',
                'system_generated': False
            },
            {
                'name': 'expenses',
                'label': 'Expenses',
                'include_total': False,
                'total_name': None,
                'total_label': None,
                'system_generated': False
            }
        ]

        # Multi-line items
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = collect_line_item_metadata(line_items, category_metadata, multi_line_items)

        # Should include: 2 line items + 1 category total + debt defined names
        expected_count = 2 + 1 + len(debt.defined_names)
        assert len(result) == expected_count

        # Check line items are included
        rev1_item = next(item for item in result if item['name'] == 'rev1')
        assert rev1_item['source_type'] == 'line_item'

        # Check category total is included
        total_rev_item = next(item for item in result if item['name'] == 'total_revenue')
        assert total_rev_item['source_type'] == 'category'

        # Check multi-line items are included
        debt_items = [item for item in result if item['source_type'] == 'multi_line_item']
        assert len(debt_items) == len(debt.defined_names)

        # Verify no duplicates
        names = [item['name'] for item in result]
        assert len(names) == len(set(names))
