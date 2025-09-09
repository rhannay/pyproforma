"""
Test cases for the validation functions in validations.py module.
"""

import pytest

from pyproforma import Category, Constraint, LineItem
from pyproforma.models.model.validations import (
    validate_categories,
    validate_constraints,
    validate_formulas,
    validate_line_items,
    validate_multi_line_items,
    validate_years,
)
from pyproforma.models.multi_line_item import Debt, ShortTermDebt


class TestValidateCategories:
    """Test the validate_categories function."""

    def test_valid_categories_pass_validation(self):
        """Test that valid categories pass validation."""
        categories = [
            Category(name="income", label="Income"),
            Category(name="expense", label="Expenses"),
        ]

        # Should not raise any exception
        validate_categories(categories)

    def test_empty_categories_pass_validation(self):
        """Test that empty categories list passes validation."""
        validate_categories([])

    def test_duplicate_category_names_raise_error(self):
        """Test that duplicate category names raise ValueError."""
        categories = [
            Category(name="income", label="Income 1"),
            Category(name="income", label="Income 2"),
            Category(name="expense", label="Expenses"),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_categories(categories)

        error_msg = str(exc_info.value)
        assert "Duplicate category names not allowed: income" in error_msg

    def test_multiple_duplicate_category_names(self):
        """Test error message when multiple category names are duplicated."""
        categories = [
            Category(name="income", label="Income 1"),
            Category(name="income", label="Income 2"),
            Category(name="expense", label="Expense 1"),
            Category(name="expense", label="Expense 2"),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_categories(categories)

        error_msg = str(exc_info.value)
        assert "Duplicate category names not allowed:" in error_msg
        assert "expense" in error_msg
        assert "income" in error_msg

    def test_categories_case_sensitive(self):
        """Test that category name validation is case sensitive."""
        categories = [
            Category(name="Income", label="Income 1"),
            Category(name="income", label="Income 2"),  # different case
        ]

        # Should not raise any exception - case matters
        validate_categories(categories)

    def test_single_category_passes_validation(self):
        """Test that a single category passes validation."""
        categories = [Category(name="income", label="Income")]

        # Should not raise any exception
        # Should not raise any exception
        validate_categories(categories)


class TestValidateLineItems:
    """Test the validate_line_items function."""

    def test_empty_line_items_pass_validation(self):
        """Test that empty line items list passes validation."""
        categories = [Category("income"), Category("expense")]
        validate_line_items([], categories)

    def test_none_line_items_pass_validation(self):
        """Test that None line items passes validation."""
        # Test with None converted to empty list - the function expects a list
        categories = [Category("income"), Category("expense")]
        validate_line_items([], categories)

    def test_valid_line_items_pass_validation(self):
        """Test that valid line items with unique names pass validation."""
        categories = [Category("income"), Category("expense")]
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs", category="expense", values={2023: 500}),
            LineItem(name="profit", category="income", values={2023: 500}),
        ]

        # Should not raise any exception
        validate_line_items(line_items, categories)

    def test_duplicate_line_item_names_raise_error(self):
        """Test that duplicate line item names raise ValueError."""
        categories = [Category("income"), Category("expense")]
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="revenue", category="expense", values={2023: 500}
            ),  # duplicate name
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_line_items(line_items, categories)

        error_msg = str(exc_info.value)
        assert "Duplicate line item names not allowed: revenue" in error_msg

    def test_multiple_duplicate_line_item_names(self):
        """Test that multiple duplicate line item names are all reported."""
        categories = [Category("income"), Category("expense")]
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="revenue", category="income", values={2023: 1200}
            ),  # duplicate name
            LineItem(name="costs", category="expense", values={2023: 500}),
            LineItem(
                name="costs", category="expense", values={2023: 600}
            ),  # duplicate name
            LineItem(name="profit", category="income", values={2023: 400}),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_line_items(line_items, categories)

        error_msg = str(exc_info.value)
        assert "Duplicate line item names not allowed:" in error_msg
        assert "costs" in error_msg
        assert "revenue" in error_msg

    def test_line_item_names_case_sensitive(self):
        """Test that line item name validation is case sensitive."""
        categories = [Category("income")]
        line_items = [
            LineItem(name="Revenue", category="income", values={2023: 1000}),
            LineItem(
                name="revenue", category="income", values={2023: 1200}
            ),  # different case
        ]

        # Should not raise any exception - case matters
        validate_line_items(line_items, categories)

    def test_single_line_item(self):
        """Test that a single line item passes validation."""
        categories = [Category("income")]
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]

        # Should not raise any exception
        validate_line_items(line_items, categories)

    def test_line_item_with_invalid_category_raises_error(self):
        """Test that line item referencing undefined category raises ValueError."""
        categories = [Category("income")]
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", values={2023: 500}
            ),  # 'expense' not in categories
        ]

        with pytest.raises(
            ValueError,
            match="Category 'expense' for LineItem 'costs' is not defined category",
        ):
            validate_line_items(line_items, categories)

    def test_multiple_line_items_with_invalid_categories_raises_error(self):
        """Test that multiple line items with undefined categories raise appropriate error."""  # noqa: E501
        categories = [Category("income")]
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", values={2023: 500}
            ),  # undefined category
            LineItem(
                name="taxes", category="liability", values={2023: 100}
            ),  # undefined category
        ]

        # Should raise error for the first invalid category encountered
        with pytest.raises(
            ValueError,
            match="Category 'expense' for LineItem 'costs' is not defined category",
        ):
            validate_line_items(line_items, categories)


class TestValidateConstraints:
    """Test the validate_constraints function."""

    def test_empty_constraints_pass_validation(self):
        """Test that empty constraints list passes validation."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        validate_constraints([], line_items)

    def test_none_constraints_pass_validation(self):
        """Test that None constraints passes validation."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        # Test with None converted to empty list - the function expects a list
        validate_constraints([], line_items)

    def test_valid_constraints_pass_validation(self):
        """Test that valid constraints pass validation."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs", category="expense", values={2023: 500}),
        ]
        constraints = [
            Constraint(
                name="revenue_min", line_item_name="revenue", target=500, operator="gt"
            ),
            Constraint(
                name="cost_max", line_item_name="costs", target=1000, operator="lt"
            ),
        ]

        # Should not raise any exception
        validate_constraints(constraints, line_items)

    def test_duplicate_constraint_names_raise_error(self):
        """Test that duplicate constraint names raise ValueError."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="revenue_check",
                line_item_name="revenue",
                target=500,
                operator="gt",
            ),
            Constraint(
                name="revenue_check",
                line_item_name="revenue",
                target=1000,
                operator="gt",
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, line_items)

        error_msg = str(exc_info.value)
        assert "Duplicate constraint names not allowed: revenue_check" in error_msg

    def test_multiple_duplicate_constraint_names(self):
        """Test error message when multiple constraint names are duplicated."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="check1", line_item_name="revenue", target=500, operator="gt"
            ),
            Constraint(
                name="check1", line_item_name="revenue", target=600, operator="gt"
            ),
            Constraint(
                name="check2", line_item_name="revenue", target=700, operator="gt"
            ),
            Constraint(
                name="check2", line_item_name="revenue", target=800, operator="gt"
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, line_items)

        error_msg = str(exc_info.value)
        assert "Duplicate constraint names not allowed:" in error_msg
        assert "check1" in error_msg
        assert "check2" in error_msg

    def test_constraint_with_invalid_line_item_raises_error(self):
        """Test that constraints referencing invalid line items raise ValueError."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="invalid_check", line_item_name="costs", target=500, operator="gt"
            )
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, line_items)

        error_msg = str(exc_info.value)
        assert (
            "Constraint 'invalid_check' references unknown line item 'costs'"
            in error_msg
        )

    def test_multiple_constraints_with_invalid_line_items(self):
        """Test that the first invalid constraint is caught."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="check1", line_item_name="costs", target=500, operator="gt"
            ),
            Constraint(
                name="check2", line_item_name="expenses", target=600, operator="gt"
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, line_items)

        error_msg = str(exc_info.value)
        # Should catch the first invalid reference
        assert "Constraint 'check1' references unknown line item 'costs'" in error_msg

    def test_constraint_names_case_sensitive(self):
        """Test that constraint names are case sensitive (no duplicates when different case)."""  # noqa: E501
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="Check", line_item_name="revenue", target=500, operator="gt"
            ),
            Constraint(
                name="check", line_item_name="revenue", target=600, operator="gt"
            ),
        ]

        # Should not raise any exception (different case = different names)
        validate_constraints(constraints, line_items)

    def test_line_item_references_case_sensitive(self):
        """Test that line item references are case sensitive."""
        line_items = [LineItem(name="Revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="check", line_item_name="revenue", target=500, operator="gt"
            )
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, line_items)

        error_msg = str(exc_info.value)
        assert "Constraint 'check' references unknown line item 'revenue'" in error_msg

    def test_constraint_with_dict_target(self):
        """Test that constraints with dict targets work correctly."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 1000})]
        constraints = [
            Constraint(
                name="revenue_check",
                line_item_name="revenue",
                target={2023: 500},
                operator="gt",
            )
        ]

        # Should not raise any exception
        validate_constraints(constraints, line_items)

    def test_empty_line_items_with_constraints_fails(self):
        """Test that constraints with empty line items fail validation."""
        constraints = [
            Constraint(
                name="check", line_item_name="revenue", target=500, operator="gt"
            )
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_constraints(constraints, [])

        error_msg = str(exc_info.value)
        assert "Constraint 'check' references unknown line item 'revenue'" in error_msg


class TestValidateMultiLineItems:
    """Test the validate_multi_line_items function."""

    def test_empty_multi_line_items_pass_validation(self):
        """Test that empty multi line items list passes validation."""
        categories = [Category("income"), Category("expense")]
        validate_multi_line_items([], categories)

    def test_none_multi_line_items_pass_validation(self):
        """Test that None multi line items passes validation."""
        # Test with None converted to empty list - the function expects a list
        categories = [Category("income"), Category("expense")]
        validate_multi_line_items([], categories)

    def test_valid_multi_line_items_pass_validation(self):
        """Test that valid multi line items pass validation."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(name="debt1", par_amount={2023: 1000}, interest_rate=0.05, term=5),
            ShortTermDebt(
                name="short_debt",
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=0.03,
            ),
        ]

        # Should not raise any exception
        validate_multi_line_items(multi_line_items, categories)

    def test_duplicate_multi_line_item_names_raise_error(self):
        """Test that duplicate multi line item names raise ValueError."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(name="debt1", par_amount={2023: 1000}, interest_rate=0.05, term=5),
            Debt(name="debt1", par_amount={2023: 2000}, interest_rate=0.04, term=3),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_multi_line_items(multi_line_items, categories)

        error_msg = str(exc_info.value)
        assert "Duplicate multi line item names not allowed: debt1" in error_msg

    def test_multiple_duplicate_multi_line_item_names(self):
        """Test error message when multiple multi line item names are duplicated."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(name="debt1", par_amount={2023: 1000}, interest_rate=0.05, term=5),
            Debt(name="debt1", par_amount={2023: 1500}, interest_rate=0.04, term=3),
            ShortTermDebt(
                name="short1", draws={}, paydown={}, begin_balance=0, interest_rate=0.03
            ),
            ShortTermDebt(
                name="short1", draws={}, paydown={}, begin_balance=0, interest_rate=0.02
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_multi_line_items(multi_line_items, categories)

        error_msg = str(exc_info.value)
        assert "Duplicate multi line item names not allowed:" in error_msg
        assert "debt1" in error_msg
        assert "short1" in error_msg

    def test_mixed_types_with_same_names_raise_error(self):
        """Test that different multi line item types with same names raise ValueError."""  # noqa: E501
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(name="debt_item", par_amount={2023: 1000}, interest_rate=0.05, term=5),
            ShortTermDebt(
                name="debt_item",
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=0.03,
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_multi_line_items(multi_line_items, categories)

        error_msg = str(exc_info.value)
        assert "Duplicate multi line item names not allowed: debt_item" in error_msg

    def test_multi_line_item_names_case_sensitive(self):
        """Test that multi line item names are case sensitive."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(name="Debt1", par_amount={2023: 1000}, interest_rate=0.05, term=5),
            Debt(name="debt1", par_amount={2023: 2000}, interest_rate=0.04, term=3),
        ]

        # Should not raise any exception (different case = different names)
        validate_multi_line_items(multi_line_items, categories)

    def test_single_multi_line_item(self):
        """Test basic case with one multi line item."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(
                name="single_debt", par_amount={2023: 1000}, interest_rate=0.05, term=5
            )
        ]

        # Should not raise any exception
        validate_multi_line_items(multi_line_items, categories)

    def test_multiple_different_multi_line_items(self):
        """Test multiple different multi line items with unique names."""
        categories = [Category("income"), Category("expense")]
        multi_line_items = [
            Debt(
                name="long_term_debt",
                par_amount={2023: 1000},
                interest_rate=0.05,
                term=10,
            ),
            Debt(
                name="equipment_loan",
                par_amount={2023: 500},
                interest_rate=0.06,
                term=5,
            ),
            ShortTermDebt(
                name="credit_line",
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=0.03,
            ),
            ShortTermDebt(
                name="working_capital",
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=0.04,
            ),
        ]

        # Should not raise any exception
        validate_multi_line_items(multi_line_items, categories)

    def test_multi_line_item_name_conflicts_with_category(self):
        """Test that multi line item names that conflict with category names raise ValueError."""  # noqa: E501
        categories = [Category("income"), Category("debt_service")]
        multi_line_items = [
            Debt(
                name="debt_service", par_amount={2023: 1000}, interest_rate=0.05, term=5
            )  # conflicts with category
        ]

        with pytest.raises(
            ValueError,
            match="Multi line item names cannot match category names: debt_service",
        ):
            validate_multi_line_items(multi_line_items, categories)

    def test_multiple_multi_line_item_category_conflicts(self):
        """Test that multiple multi line item names conflicting with categories are reported."""  # noqa: E501
        categories = [
            Category("income"),
            Category("debt_service"),
            Category("expenses"),
        ]
        multi_line_items = [
            Debt(
                name="debt_service", par_amount={2023: 1000}, interest_rate=0.05, term=5
            ),  # conflicts
            ShortTermDebt(
                name="income", draws={}, paydown={}, begin_balance=0, interest_rate=0.03
            ),  # conflicts
            Debt(
                name="valid_debt", par_amount={2023: 500}, interest_rate=0.04, term=3
            ),  # no conflict
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_multi_line_items(multi_line_items, categories)

        error_msg = str(exc_info.value)
        assert "Multi line item names cannot match category names:" in error_msg
        assert "debt_service" in error_msg
        assert "income" in error_msg


class TestValidateFormulas:
    """Test the validate_formulas function."""

    def test_empty_line_items_pass_validation(self):
        """Test that empty line items list passes validation."""
        validate_formulas([], [])

    def test_none_line_items_pass_validation(self):
        """Test that None line items passes validation."""
        # Test with None converted to empty list - the function expects a list
        validate_formulas([], [])

    def test_line_items_without_formulas_pass_validation(self):
        """Test that line items without formulas pass validation."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs", category="expense", values={2023: 500}),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_valid_formulas_pass_validation(self):
        """Test that line items with valid formulas pass validation."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs", category="expense", formula="revenue * 0.8"),
            LineItem(name="profit", category="income", formula="revenue - costs"),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
            {
                "name": "profit",
                "label": "Profit",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "profit",
                "category": "income",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_formula_with_undefined_variable_raises_error(self):
        """Test that formulas with undefined variables raise ValueError."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", formula="revenue * unknown_variable"
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_formulas(line_items, metadata)

        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'costs'" in error_msg
        assert "unknown_variable" in error_msg

    def test_multiple_undefined_variables_in_formula(self):
        """Test error message when formula has multiple undefined variables."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs",
                category="expense",
                formula="missing_a + missing_b + revenue",
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_formulas(line_items, metadata)

        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'costs'" in error_msg
        assert "missing_a" in error_msg
        assert "missing_b" in error_msg

    def test_time_offset_formulas_pass_validation(self):
        """Test that valid time-offset formulas pass validation."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="growth", category="metrics", formula="revenue - revenue[-1]"
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "growth",
                "label": "Growth",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "growth",
                "category": "metrics",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_time_offset_formula_with_undefined_variable_raises_error(self):
        """Test that time-offset formulas with undefined variables raise ValueError."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="growth", category="metrics", formula="revenue - unknown_var[-1]"
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "growth",
                "label": "Growth",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "growth",
                "category": "metrics",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_formulas(line_items, metadata)

        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'growth'" in error_msg
        assert "unknown_var" in error_msg

    def test_formula_with_category_totals(self):
        """Test that formulas can reference category totals from metadata."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="margin", category="metrics", formula="total_income * 0.1"),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "total_income",
                "label": "Total Income",
                "value_format": "no_decimals",
                "source_type": "category",
                "source_name": "income",
                "category": None,
            },
            {
                "name": "margin",
                "label": "Margin",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "margin",
                "category": "metrics",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_formula_with_multi_line_item_references(self):
        """Test that formulas can reference multi line item outputs from metadata."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="debt_service_coverage",
                category="metrics",
                formula="revenue / debt_interest_expense",
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "debt_interest_expense",
                "label": "Debt Interest Expense",
                "value_format": "no_decimals",
                "source_type": "multi_line_item",
                "source_name": "debt1",
                "category": None,
            },
            {
                "name": "debt_service_coverage",
                "label": "Debt Service Coverage",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "debt_service_coverage",
                "category": "metrics",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_empty_formula_ignored(self):
        """Test that empty formulas are ignored."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs", category="expense", formula="", values={2023: 500}),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_none_formula_ignored(self):
        """Test that None formulas are ignored."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", formula=None, values={2023: 500}
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_whitespace_only_formula_ignored(self):
        """Test that whitespace-only formulas are ignored."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", formula="   ", values={2023: 500}
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_complex_formula_validation(self):
        """Test validation of complex formulas with multiple operations."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="cogs", category="expense", formula="revenue * 0.4"),
            LineItem(name="opex", category="expense", formula="revenue * 0.3"),
            LineItem(name="tax_rate", category="assumption", values={2023: 0.25}),
            LineItem(
                name="net_income",
                category="income",
                formula="(revenue - cogs - opex) * (1 - tax_rate)",
            ),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "cogs",
                "label": "COGS",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "cogs",
                "category": "expense",
            },
            {
                "name": "opex",
                "label": "OpEx",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "opex",
                "category": "expense",
            },
            {
                "name": "tax_rate",
                "label": "Tax Rate",
                "value_format": "percent",
                "source_type": "line_item",
                "source_name": "tax_rate",
                "category": "assumption",
            },
            {
                "name": "net_income",
                "label": "Net Income",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "net_income",
                "category": "income",
            },
        ]

        # Should not raise any exception
        validate_formulas(line_items, metadata)

    def test_formula_variables_case_sensitive(self):
        """Test that formula variable references are case sensitive."""
        line_items = [
            LineItem(name="Revenue", category="income", values={2023: 1000}),
            LineItem(
                name="costs", category="expense", formula="revenue * 0.8"
            ),  # lowercase 'revenue'
        ]
        metadata = [
            {
                "name": "Revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "Revenue",
                "category": "income",
            },
            {
                "name": "costs",
                "label": "Costs",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs",
                "category": "expense",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_formulas(line_items, metadata)

        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'costs'" in error_msg
        assert "revenue" in error_msg

    def test_multiple_line_items_with_formula_errors(self):
        """Test that the first line item with formula error is caught."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 1000}),
            LineItem(name="costs1", category="expense", formula="unknown_var1 * 0.8"),
            LineItem(name="costs2", category="expense", formula="unknown_var2 * 0.9"),
        ]
        metadata = [
            {
                "name": "revenue",
                "label": "Revenue",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "revenue",
                "category": "income",
            },
            {
                "name": "costs1",
                "label": "Costs1",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs1",
                "category": "expense",
            },
            {
                "name": "costs2",
                "label": "Costs2",
                "value_format": None,
                "source_type": "line_item",
                "source_name": "costs2",
                "category": "expense",
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            validate_formulas(line_items, metadata)

        error_msg = str(exc_info.value)
        # Should catch the first formula error
        assert "Error in formula for line item 'costs1'" in error_msg
        assert "unknown_var1" in error_msg


class TestValidateYears:
    """Test the validate_years function."""

    def test_empty_years_pass_validation(self):
        """Test that empty years list passes validation."""
        # Empty years should be allowed for template models
        validate_years([])

    def test_single_year_passes_validation(self):
        """Test that a single year passes validation."""
        validate_years([2023])

    def test_valid_sequential_years_pass_validation(self):
        """Test that valid sequential years pass validation."""
        validate_years([2020, 2021, 2022, 2023])
        validate_years([2023, 2024])
        validate_years([1999, 2000, 2001])

    def test_non_integer_years_raise_error(self):
        """Test that non-integer years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020.5, 2021, 2022])

        error_msg = str(exc_info.value)
        assert "All years must be integers" in error_msg
        assert "2020.5" in error_msg
        assert "float" in error_msg

    def test_string_years_raise_error(self):
        """Test that string years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years(["2020", 2021, 2022])

        error_msg = str(exc_info.value)
        assert "All years must be integers" in error_msg
        assert "2020" in error_msg
        assert "str" in error_msg

    def test_mixed_type_years_raise_error(self):
        """Test that mixed type years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2021.0, "2022", 2023])

        error_msg = str(exc_info.value)
        assert "All years must be integers" in error_msg
        # Should catch the first non-integer type
        assert "2021.0" in error_msg

    def test_unsorted_years_raise_error(self):
        """Test that unsorted years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2023, 2020, 2021, 2022])

        error_msg = str(exc_info.value)
        assert "Years must be in ascending order" in error_msg
        assert "[2023, 2020, 2021, 2022]" in error_msg

    def test_reverse_sorted_years_raise_error(self):
        """Test that reverse sorted years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2023, 2022, 2021, 2020])

        error_msg = str(exc_info.value)
        assert "Years must be in ascending order" in error_msg

    def test_partially_unsorted_years_raise_error(self):
        """Test that partially unsorted years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2022, 2021, 2023])

        error_msg = str(exc_info.value)
        assert "Years must be in ascending order" in error_msg

    def test_gap_in_years_raises_error(self):
        """Test that gaps in sequential years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2022, 2023])  # Missing 2021

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg
        assert "Gap found between 2020 and 2022" in error_msg

    def test_multiple_gaps_in_years_raise_error(self):
        """Test that the first gap is reported when multiple gaps exist."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2022, 2024])  # Missing 2021 and 2023

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg
        assert "Gap found between 2020 and 2022" in error_msg

    def test_large_gap_in_years_raises_error(self):
        """Test that large gaps in years raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2025])  # 4-year gap

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg
        assert "Gap found between 2020 and 2025" in error_msg

    def test_duplicate_years_raise_error(self):
        """Test that duplicate years raise ValueError (via sorting check)."""
        # Duplicate years will fail the sorting check since
        # [2020, 2020, 2021] != sorted([2020, 2020, 2021])
        # Actually, sorted([2020, 2020, 2021]) == [2020, 2020, 2021],
        # so this might not fail sorting
        # Let's test what actually happens
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2020, 2021])

        error_msg = str(exc_info.value)
        # This should fail on the gap check since 2020 != 2020 + 1
        assert "Years must be sequential with no gaps" in error_msg

    def test_negative_years_pass_validation(self):
        """Test that negative years are allowed if they are sequential."""
        validate_years([-2, -1, 0, 1])
        validate_years([-10, -9, -8])

    def test_negative_years_with_gaps_raise_error(self):
        """Test that negative years with gaps raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([-5, -3, -2])  # Missing -4

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg
        assert "Gap found between -5 and -3" in error_msg

    def test_very_large_years_pass_validation(self):
        """Test that very large years pass validation if sequential."""
        validate_years([9998, 9999, 10000])

    def test_very_small_years_pass_validation(self):
        """Test that very small years pass validation if sequential."""
        validate_years([-1000, -999, -998])

    def test_none_years_list_raises_error(self):
        """Test that None as years list raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            validate_years(None)

        error_msg = str(exc_info.value)
        assert "Years cannot be None" in error_msg

    def test_years_comprehensive_validation_order(self):
        """Test that validation checks happen in the expected order."""
        # Integer check should happen first
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020.5, 2019, 2021])  # Float, unsorted, gap

        error_msg = str(exc_info.value)
        # Should fail on integer check first
        assert "All years must be integers" in error_msg

    def test_sorted_but_with_gaps_fails_appropriately(self):
        """Test that years that are sorted but have gaps fail with gap message."""
        with pytest.raises(ValueError) as exc_info:
            validate_years([2020, 2021, 2023, 2024])  # Missing 2022

        error_msg = str(exc_info.value)
        assert "Years must be sequential with no gaps" in error_msg
        assert "Gap found between 2021 and 2023" in error_msg

    def test_zero_year_included_in_sequence(self):
        """Test that year zero can be included in valid sequences."""
        validate_years([-1, 0, 1])
        validate_years([0, 1, 2])

    def test_boundary_conditions_with_single_elements(self):
        """Test boundary conditions with various single year values."""
        validate_years([0])
        validate_years([-1])
        validate_years([2023])
        validate_years([10000])
