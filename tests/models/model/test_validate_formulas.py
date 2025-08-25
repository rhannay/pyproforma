"""
Test cases for the Model._validate_formulas() method.
"""

import pytest
from pyproforma import Model, LineItem, Category


class TestModelValidateFormulas:
    """Test the _validate_formulas method in Model class."""

    def test_valid_formulas_pass_validation(self):
        """Test that models with valid formulas pass validation."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        expenses = LineItem(name='expenses', category='expense', formula='revenue * 0.8')
        profit = LineItem(name='profit', category='income', formula='revenue - expenses')
        
        # Should not raise any exception
        model = Model(line_items=[revenue, expenses, profit], years=[2023])
        
        # Verify the model works correctly
        assert model.value('revenue', 2023) == 1000
        assert model.value('expenses', 2023) == 800.0
        assert model.value('profit', 2023) == 200.0

    def test_invalid_formula_raises_error(self):
        """Test that models with invalid formulas raise ValueError during initialization."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        invalid_expense = LineItem(name='expenses', category='expense', formula='revenue * unknown_variable')
        
        with pytest.raises(ValueError) as exc_info:
            Model(line_items=[revenue, invalid_expense], years=[2023])
        
        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'expenses'" in error_msg
        assert "Formula contains undefined line item names: unknown_variable" in error_msg

    def test_multiple_invalid_variables_in_formula(self):
        """Test error message when formula has multiple undefined variables."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        invalid_item = LineItem(name='invalid', category='expense', formula='missing_a + missing_b + revenue')
        
        with pytest.raises(ValueError) as exc_info:
            Model(line_items=[revenue, invalid_item], years=[2023])
        
        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'invalid'" in error_msg
        assert "missing_a" in error_msg
        assert "missing_b" in error_msg

    def test_time_offset_formula_validation(self):
        """Test that time-offset formulas are validated correctly."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000, 2024: 1100})
        
        # Valid time-offset formula should pass validation
        growth = LineItem(name='growth', category='metrics', formula='revenue - revenue[-1]')
        # This should pass validation (even though it might fail at runtime due to missing data)
        try:
            Model(line_items=[revenue, growth], years=[2024])  # Only 2024 to avoid runtime issues
        except ValueError as e:
            if "Formula contains undefined line item names" in str(e):
                pytest.fail(f"Valid time-offset formula should pass validation: {e}")
        
        # Invalid time-offset formula should fail validation
        invalid_growth = LineItem(name='invalid_growth', category='metrics', formula='revenue - unknown_var[-1]')
        
        with pytest.raises(ValueError) as exc_info:
            Model(line_items=[revenue, invalid_growth], years=[2023])
        
        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'invalid_growth'" in error_msg
        assert "unknown_var" in error_msg

    def test_category_totals_in_formulas(self):
        """Test that formulas can correctly reference category totals."""
        rev1 = LineItem(name='rev1', category='revenue', values={2023: 600})
        rev2 = LineItem(name='rev2', category='revenue', values={2023: 400})
        margin = LineItem(name='margin', category='metrics', formula='total_revenue * 0.1')
        
        revenue_cat = Category(name='revenue', include_total=True)
        metrics_cat = Category(name='metrics', include_total=False)
        
        # Should not raise any exception
        model = Model(
            line_items=[rev1, rev2, margin],
            categories=[revenue_cat, metrics_cat],
            years=[2023]
        )
        
        # Verify it works correctly
        assert model.value('total_revenue', 2023) == 1000
        assert model.value('margin', 2023) == 100.0

    def test_empty_and_none_formulas_ignored(self):
        """Test that empty and None formulas are not validated."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        empty_formula = LineItem(name='empty', category='expense', formula='', values={2023: 100})
        none_formula = LineItem(name='none_item', category='expense', formula=None, values={2023: 50})
        whitespace_formula = LineItem(name='whitespace', category='expense', formula='   ', values={2023: 25})
        
        # Should not raise any exception
        model = Model(
            line_items=[revenue, empty_formula, none_formula, whitespace_formula],
            years=[2023]
        )
        
        # Verify the model works
        assert model.value('revenue', 2023) == 1000
        assert model.value('empty', 2023) == 100
        assert model.value('none_item', 2023) == 50
        assert model.value('whitespace', 2023) == 25

    def test_formula_validation_called_in_recalculate(self):
        """Test that _validate_formulas is called during _recalculate."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        expenses = LineItem(name='expenses', category='expense', formula='revenue * 0.8')
        
        model = Model(line_items=[revenue, expenses], years=[2023])
        
        # Manually add an invalid line item to test recalculate validation
        invalid_item = LineItem(name='invalid', category='expense', formula='unknown_var * 2')
        model._line_item_definitions.append(invalid_item)
        
        # _recalculate should catch the invalid formula
        with pytest.raises(ValueError) as exc_info:
            model._recalculate()
        
        error_msg = str(exc_info.value)
        assert "Error in formula for line item 'invalid'" in error_msg
        assert "unknown_var" in error_msg

    def test_complex_formula_validation(self):
        """Test validation of complex formulas with multiple operations."""
        revenue = LineItem(name='revenue', category='income', values={2023: 1000})
        cogs = LineItem(name='cogs', category='expense', formula='revenue * 0.4')
        opex = LineItem(name='opex', category='expense', formula='revenue * 0.3')
        tax_rate = LineItem(name='tax_rate', category='assumption', values={2023: 0.25})
        
        # Complex formula with parentheses and multiple variables
        net_income = LineItem(
            name='net_income', 
            category='income', 
            formula='(revenue - cogs - opex) * (1 - tax_rate)'
        )
        
        # Should not raise any exception
        model = Model(
            line_items=[revenue, cogs, opex, tax_rate, net_income],
            years=[2023]
        )
        
        # Verify it calculates correctly
        assert model.value('net_income', 2023) == 225.0  # (1000 - 400 - 300) * (1 - 0.25)
