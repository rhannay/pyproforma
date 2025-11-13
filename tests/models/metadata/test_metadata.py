"""
Tests for metadata collection utilities.

This module tests the metadata collection functions for categories and line items,
including their integration with multi-line items.
"""

import pytest

from pyproforma import Category, Constraint, LineItem
from pyproforma.models.metadata import (
    generate_category_metadata,
    generate_constraint_metadata,
    generate_line_item_metadata,
)
from pyproforma.models.generator.debt import Debt


class TestGenerateCategoryMetadata:
    """Test the generate_category_metadata function."""

    def test_empty_categories_and_multi_line_items(self):
        """Test with empty input lists."""
        result = generate_category_metadata([], [])
        assert result == []

        result = generate_category_metadata([])
        assert result == []

    def test_single_category_without_total(self):
        """Test with a single category."""
        categories = [Category(name="revenue", label="Revenue")]
        result = generate_category_metadata(categories)

        expected = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            }
        ]
        assert result == expected

    def test_single_category_with_label(self):
        """Test with a single category that has a label."""
        categories = [
            Category(
                name="expenses",
                label="Expenses",
            )
        ]
        result = generate_category_metadata(categories)

        expected = [
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
        ]
        assert result == expected

    def test_multiple_categories_mixed_totals(self):
        """Test with multiple categories."""
        categories = [
            Category(name="revenue", label="Revenue"),
            Category(
                name="expenses",
                label="Expenses",
            ),
            Category(
                name="assets",
                label="Assets",
            ),
        ]
        result = generate_category_metadata(categories)

        expected = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            },
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
            {
                "name": "assets",
                "label": "Assets",
                "system_generated": False,
            },
        ]
        assert result == expected

    def test_with_multi_line_items(self):
        """Test with multi-line items included."""
        categories = [Category(name="revenue", label="Revenue")]
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = generate_category_metadata(categories, multi_line_items)

        expected = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            },
            {
                "name": "debt",
                "label": "debt (Generator)",
                "system_generated": True,
            },
        ]
        assert result == expected

    def test_duplicate_multi_line_item_name_ignored(self):
        """Test that multi-line items with existing category names are ignored."""
        categories = [Category(name="debt", label="Debt Category")]
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = generate_category_metadata(categories, multi_line_items)

        # Should only have the original category, not the multi-line item
        expected = [
            {
                "name": "debt",
                "label": "Debt Category",
                "system_generated": False,
            }
        ]
        assert result == expected

    def test_multiple_multi_line_items(self):
        """Test with multiple multi-line items."""
        categories = []
        debt1 = Debt(name="debt1", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        debt2 = Debt(name="debt2", par_amount={2020: 2000}, interest_rate=0.06, term=25)
        multi_line_items = [debt1, debt2]

        result = generate_category_metadata(categories, multi_line_items)

        expected = [
            {
                "name": "debt1",
                "label": "debt1 (Generator)",
                "system_generated": True,
            },
            {
                "name": "debt2",
                "label": "debt2 (Generator)",
                "system_generated": True,
            },
        ]
        assert result == expected


class TestGenerateLineItemMetadata:
    """Test the generate_line_item_metadata function."""

    def test_empty_inputs(self):
        """Test with empty input lists."""
        result = generate_line_item_metadata([], [], [])
        assert result == []

    def test_single_line_item(self):
        """Test with a single line item."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2020: 1000},
                value_format="no_decimals",
            )
        ]
        category_metadata = []
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        expected = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": "no_decimals",
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
                "formula": None,
                "hardcoded_values": {2020: 1000},
            }
        ]
        assert result == expected

    def test_multiple_line_items_different_formats(self):
        """Test with multiple line items with different value formats."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2020: 1000},
                value_format="no_decimals",
            ),
            LineItem(
                name="growth_rate",
                label="Growth Rate",
                category="assumptions",
                values={2020: 0.05},
                value_format="percent",
            ),
            LineItem(
                name="description",
                label="Description",
                category="notes",
                values={2020: "test"},
                value_format="str",
            ),
        ]
        category_metadata = []
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        expected = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": "no_decimals",
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
                "formula": None,
                "hardcoded_values": {2020: 1000},
            },
            {
                "name": "growth_rate",
                "label": "Growth Rate",
                "value_format": "percent",
                "source_type": "line_item",
                "source_name": "growth_rate",
                "category": "assumptions",
                "formula": None,
                "hardcoded_values": {2020: 0.05},
            },
            {
                "name": "description",
                "label": "Description",
                "value_format": "str",
                "source_type": "line_item",
                "source_name": "description",
                "category": "notes",
                "formula": None,
                "hardcoded_values": {2020: "test"},
            },
        ]
        assert result == expected

    def test_line_item_with_formula(self):
        """Test with a line item that has a formula."""
        line_items = [
            LineItem(
                name="profit",
                label="Profit",
                category="income",
                formula="revenue * 0.1",
                values={2020: 100, 2021: 200},
                value_format="no_decimals",
            )
        ]
        category_metadata = []
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        expected = [
            {
                "name": "profit",
                "label": "Profit",
                "value_format": "no_decimals",
                "source_type": "line_item",
                "source_name": "profit",
                "category": "income",
                "formula": "revenue * 0.1",
                "hardcoded_values": {2020: 100, 2021: 200},
            }
        ]
        assert result == expected

    def test_line_item_formula_only_no_hardcoded_values(self):
        """Test with a line item that has only a formula and no hardcoded values."""
        line_items = [
            LineItem(
                name="calculated_value",
                label="Calculated Value",
                category="calculations",
                formula="base_value + adjustment",
                value_format="two_decimals",
            )
        ]
        category_metadata = []
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        expected = [
            {
                "name": "calculated_value",
                "label": "Calculated Value",
                "value_format": "two_decimals",
                "source_type": "line_item",
                "source_name": "calculated_value",
                "category": "calculations",
                "formula": "base_value + adjustment",
                "hardcoded_values": {},
            }
        ]
        assert result == expected

    def test_category_totals_not_included(self):
        """Test that category totals are not automatically created."""
        line_items = [
            LineItem(
                name="rev1", label="Revenue 1", category="revenue", values={2020: 1000}
            ),
            LineItem(
                name="rev2", label="Revenue 2", category="revenue", values={2020: 2000}
            ),
            LineItem(
                name="exp1", label="Expense 1", category="expenses", values={2020: 500}
            ),
        ]
        category_metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            },
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
        ]
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        # Should only include line items, no category totals
        assert len(result) == 3  # 3 line items only
        names = [item["name"] for item in result]
        assert "rev1" in names
        assert "rev2" in names
        assert "exp1" in names

    def test_line_items_only(self):
        """Test that only line items are included when no totals configured."""
        line_items = [
            LineItem(
                name="rev1", label="Revenue 1", category="revenue", values={2020: 1000}
            )
        ]
        category_metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            },
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
        ]
        multi_line_items = []

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        # Should include only the line item
        assert len(result) == 1
        names = [item["name"] for item in result]
        assert "rev1" in names

    def test_multi_line_items_included(self):
        """Test that multi-line items are included in metadata."""
        line_items = []
        category_metadata = []
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        # Should include all defined names from the debt multi-line item
        # with "generator_name.field" format
        debt_field_names = debt.defined_names
        assert len(result) == len(debt_field_names)

        for field_name in debt_field_names:
            full_name = f"debt.{field_name}"
            matching_item = next(item for item in result if item["name"] == full_name)
            assert matching_item == {
                "name": full_name,
                "label": full_name,
                "value_format": "no_decimals",
                "source_type": "generator",
                "source_name": "debt",
                "category": "debt",
                "formula": None,
                "hardcoded_values": None,
            }

    def test_duplicate_names_raise_error(self):
        """Test that duplicate names raise a ValueError."""
        line_items = [
            LineItem(
                name="revenue", label="Revenue", category="income", values={2020: 1000}
            ),
            LineItem(
                name="revenue", label="Revenue2", category="income", values={2020: 2000}
            ),
        ]
        category_metadata = [
            {
                "name": "income",
                "label": "Income",
                "system_generated": False,
            }
        ]
        multi_line_items = []

        with pytest.raises(ValueError) as exc_info:
            generate_line_item_metadata(line_items, category_metadata, multi_line_items)

        assert "Duplicate defined names found in Model: revenue" in str(exc_info.value)

    def test_multiple_duplicate_names_raise_error(self):
        """Test that multiple duplicate names are all reported in the error."""
        line_items = [
            LineItem(
                name="revenue", label="Revenue", category="income", values={2020: 1000}
            ),
            LineItem(
                name="revenue", label="Revenue2", category="income", values={2020: 2000}
            ),
            LineItem(
                name="cost", label="Cost", category="expenses", values={2020: 500}
            ),
            LineItem(
                name="cost", label="Cost2", category="expenses", values={2020: 600}
            ),
        ]
        category_metadata = [
            {
                "name": "income",
                "label": "Income",
                "system_generated": False,
            },
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
        ]
        multi_line_items = []

        with pytest.raises(ValueError) as exc_info:
            generate_line_item_metadata(line_items, category_metadata, multi_line_items)

        error_msg = str(exc_info.value)
        assert "Duplicate defined names found in Model:" in error_msg
        assert "revenue" in error_msg
        assert "cost" in error_msg

    def test_comprehensive_integration(self):
        """Test with a comprehensive mix of all component types."""
        # Line items
        line_items = [
            LineItem(
                name="rev1", label="Revenue 1", category="revenue", values={2020: 1000}
            ),
            LineItem(
                name="exp1", label="Expense 1", category="expenses", values={2020: 500}
            ),
        ]

        # Category metadata
        category_metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "system_generated": False,
            },
            {
                "name": "expenses",
                "label": "Expenses",
                "system_generated": False,
            },
        ]

        # Multi-line items
        debt = Debt(name="debt", par_amount={2020: 1000}, interest_rate=0.05, term=30)
        multi_line_items = [debt]

        result = generate_line_item_metadata(
            line_items, category_metadata, multi_line_items
        )

        # Should include: 2 line items + debt defined names
        expected_count = 2 + len(debt.defined_names)
        assert len(result) == expected_count

        # Check line items are included
        rev1_item = next(item for item in result if item["name"] == "rev1")
        assert rev1_item["source_type"] == "line_item"

        # Check generators are included
        debt_items = [
            item for item in result if item["source_type"] == "generator"
        ]
        assert len(debt_items) == len(debt.defined_names)

        # Verify no duplicates
        names = [item["name"] for item in result]
        assert len(names) == len(set(names))


class TestGenerateConstraintMetadata:
    """Test the generate_constraint_metadata function."""

    def test_empty_constraints(self):
        """Test with empty input list."""
        result = generate_constraint_metadata([])
        assert result == []

    def test_single_constraint_with_float_target(self):
        """Test with a single constraint with a float target."""
        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
                tolerance=0.0,
                label="Minimum Revenue",
            )
        ]
        result = generate_constraint_metadata(constraints)

        expected = [
            {
                "name": "min_revenue",
                "label": "Minimum Revenue",
                "line_item_name": "revenue",
                "target": 50000.0,
                "operator": "gt",
                "operator_symbol": ">",
                "tolerance": 0.0,
            }
        ]
        assert result == expected

    def test_single_constraint_with_dict_target(self):
        """Test with a single constraint with a dictionary target."""
        constraints = [
            Constraint(
                name="revenue_budget",
                line_item_name="revenue",
                target={2020: 100000.0, 2021: 110000.0},
                operator="le",
                tolerance=1000.0,
                label="Revenue Budget Constraint",
            )
        ]
        result = generate_constraint_metadata(constraints)

        expected = [
            {
                "name": "revenue_budget",
                "label": "Revenue Budget Constraint",
                "line_item_name": "revenue",
                "target": {2020: 100000.0, 2021: 110000.0},
                "operator": "le",
                "operator_symbol": "<=",
                "tolerance": 1000.0,
            }
        ]
        assert result == expected

    def test_constraint_without_label(self):
        """Test with a constraint that doesn't have a custom label."""
        constraints = [
            Constraint(
                name="balance_check",
                line_item_name="balance",
                target=0.0,
                operator="eq",
                tolerance=0.01,
                # No label provided - should use name as label
            )
        ]
        result = generate_constraint_metadata(constraints)

        expected = [
            {
                "name": "balance_check",
                "label": "balance_check",  # Should use name as label
                "line_item_name": "balance",
                "target": 0.0,
                "operator": "eq",
                "operator_symbol": "=",
                "tolerance": 0.01,
            }
        ]
        assert result == expected

    def test_multiple_constraints_different_operators(self):
        """Test with multiple constraints using different operators."""
        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
                label="Minimum Revenue",
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=30000.0,
                operator="le",
                tolerance=500.0,
                label="Maximum Expenses",
            ),
            Constraint(
                name="balance_zero",
                line_item_name="balance",
                target=0.0,
                operator="eq",
                tolerance=0.01,
                label="Balance Check",
            ),
            Constraint(
                name="profit_not_zero",
                line_item_name="profit",
                target=0.0,
                operator="ne",
                tolerance=100.0,
                label="Profit Non-Zero",
            ),
        ]
        result = generate_constraint_metadata(constraints)

        expected = [
            {
                "name": "min_revenue",
                "label": "Minimum Revenue",
                "line_item_name": "revenue",
                "target": 50000.0,
                "operator": "gt",
                "operator_symbol": ">",
                "tolerance": 0.0,
            },
            {
                "name": "max_expenses",
                "label": "Maximum Expenses",
                "line_item_name": "expenses",
                "target": 30000.0,
                "operator": "le",
                "operator_symbol": "<=",
                "tolerance": 500.0,
            },
            {
                "name": "balance_zero",
                "label": "Balance Check",
                "line_item_name": "balance",
                "target": 0.0,
                "operator": "eq",
                "operator_symbol": "=",
                "tolerance": 0.01,
            },
            {
                "name": "profit_not_zero",
                "label": "Profit Non-Zero",
                "line_item_name": "profit",
                "target": 0.0,
                "operator": "ne",
                "operator_symbol": "!=",
                "tolerance": 100.0,
            },
        ]
        assert result == expected

    def test_all_operators_covered(self):
        """Test that all supported operators work correctly."""
        constraints = [
            Constraint("eq_constraint", "item1", 100.0, "eq"),
            Constraint("lt_constraint", "item2", 200.0, "lt"),
            Constraint("le_constraint", "item3", 300.0, "le"),
            Constraint("gt_constraint", "item4", 400.0, "gt"),
            Constraint("ge_constraint", "item5", 500.0, "ge"),
            Constraint("ne_constraint", "item6", 600.0, "ne"),
        ]
        result = generate_constraint_metadata(constraints)

        expected_operators = [
            ("eq", "="),
            ("lt", "<"),
            ("le", "<="),
            ("gt", ">"),
            ("ge", ">="),
            ("ne", "!="),
        ]

        assert len(result) == 6
        for i, (op, symbol) in enumerate(expected_operators):
            assert result[i]["operator"] == op
            assert result[i]["operator_symbol"] == symbol

    def test_constraints_with_zero_tolerance(self):
        """Test constraints with zero tolerance (default)."""
        constraints = [
            Constraint(
                name="exact_match",
                line_item_name="value",
                target=1000.0,
                operator="eq",
                # tolerance defaults to 0.0
            )
        ]
        result = generate_constraint_metadata(constraints)

        assert result[0]["tolerance"] == 0.0

    def test_constraints_with_custom_tolerance(self):
        """Test constraints with custom tolerance values."""
        constraints = [
            Constraint(
                name="approx_match",
                line_item_name="value",
                target=1000.0,
                operator="eq",
                tolerance=5.0,
            )
        ]
        result = generate_constraint_metadata(constraints)

        assert result[0]["tolerance"] == 5.0

    def test_constraint_preserves_all_attributes(self):
        """Test that all constraint attributes are preserved in metadata."""
        constraint = Constraint(
            name="complex_constraint",
            line_item_name="complex_item",
            target={2020: 1000.0, 2021: 1100.0, 2022: 1200.0},
            operator="ge",
            tolerance=50.0,
            label="Complex Multi-Year Constraint",
        )
        result = generate_constraint_metadata([constraint])

        assert len(result) == 1
        metadata = result[0]

        assert metadata["name"] == "complex_constraint"
        assert metadata["label"] == "Complex Multi-Year Constraint"
        assert metadata["line_item_name"] == "complex_item"
        assert metadata["target"] == {2020: 1000.0, 2021: 1100.0, 2022: 1200.0}
        assert metadata["operator"] == "ge"
        assert metadata["operator_symbol"] == ">="
        assert metadata["tolerance"] == 50.0
