"""
Tests for LineItemSelection.
"""

import pytest

from pyproforma.table import Table
from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


class TestLineItemSelection:
    """Tests for selecting line items."""

    def test_select_single_item(self):
        """Test selecting a single line item."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue"])
        assert selection.names == ["revenue"]

    def test_select_multiple_items(self):
        """Test selecting multiple line items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses", "profit"])
        assert selection.names == ["revenue", "expenses", "profit"]

    def test_select_preserves_order(self):
        """Test that selection preserves the order of names."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024])

        # Select in non-alphabetical order
        selection = model.select(["profit", "revenue", "expenses"])
        assert selection.names == ["profit", "revenue", "expenses"]

    def test_select_invalid_name_single(self):
        """Test that selecting an invalid name raises ValueError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(ValueError, match="Line item\\(s\\) not found in model: invalid"):
            model.select(["invalid"])

    def test_select_invalid_name_multiple(self):
        """Test that selecting multiple invalid names raises ValueError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(
            ValueError, match="Line item\\(s\\) not found in model: invalid1, invalid2"
        ):
            model.select(["invalid1", "invalid2"])

    def test_select_mixed_valid_invalid(self):
        """Test that selecting a mix of valid and invalid names raises ValueError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        model = TestModel(periods=[2024])

        with pytest.raises(
            ValueError, match="Line item\\(s\\) not found in model: invalid"
        ):
            model.select(["revenue", "invalid"])

    def test_select_empty_list(self):
        """Test selecting with an empty list."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        selection = model.select([])
        assert selection.names == []

    def test_select_all_items(self):
        """Test selecting all line items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024])

        # Select all items using model.line_item_names
        selection = model.select(model.line_item_names)
        assert len(selection.names) == 3
        assert "revenue" in selection.names
        assert "expenses" in selection.names
        assert "profit" in selection.names

    def test_selection_repr(self):
        """Test string representation of selection."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses"])
        repr_str = repr(selection)
        assert "LineItemSelection" in repr_str
        assert "revenue" in repr_str
        assert "expenses" in repr_str


class TestLineItemSelectionValue:
    """Tests for selection.value() method."""

    def test_value_single_item(self):
        """Test getting value for single selected item."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue"])
        result = selection.value(2024)
        assert result == {"revenue": 100}

    def test_value_multiple_items(self):
        """Test getting values for multiple selected items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses", "profit"])
        result = selection.value(2024)
        assert result == {"revenue": 100, "expenses": 60, "profit": 40}

    def test_value_different_periods(self):
        """Test getting values for different periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses"])
        
        result_2024 = selection.value(2024)
        assert result_2024 == {"revenue": 100, "expenses": 60}
        
        result_2025 = selection.value(2025)
        assert result_2025 == {"revenue": 110, "expenses": 66}

    def test_value_preserves_order(self):
        """Test that value dict preserves selection order."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024])

        # Select in specific order
        selection = model.select(["profit", "revenue", "expenses"])
        result = selection.value(2024)
        
        # Dict should maintain insertion order (Python 3.7+)
        assert list(result.keys()) == ["profit", "revenue", "expenses"]
        assert result == {"profit": 40, "revenue": 100, "expenses": 60}

    def test_value_invalid_period(self):
        """Test that invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        selection = model.select(["revenue"])
        with pytest.raises(KeyError, match="Period 2025 not found"):
            selection.value(2025)

    def test_value_empty_selection(self):
        """Test getting values with empty selection."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        selection = model.select([])
        result = selection.value(2024)
        assert result == {}


class TestLineItemSelectionSum:
    """Tests for selection.sum() method."""

    def test_sum_single_item(self):
        """Test summing a single selected item."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue"])
        assert selection.sum(2024) == 100
        assert selection.sum(2025) == 110

    def test_sum_multiple_items(self):
        """Test summing multiple selected items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses"])
        assert selection.sum(2024) == 160  # 100 + 60
        assert selection.sum(2025) == 176  # 110 + 66

    def test_sum_with_tag_selection(self):
        """Test summing items selected by tag."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110}, tags=["income"])
            interest = FixedLine(values={2024: 5, 2025: 6}, tags=["income"])
            expenses = FixedLine(values={2024: 60, 2025: 66}, tags=["expense"])

        model = TestModel(periods=[2024, 2025])

        # Sum income items
        income_selection = model.tag["income"]
        assert income_selection.sum(2024) == 105  # 100 + 5
        assert income_selection.sum(2025) == 116  # 110 + 6

        # Sum expense items
        expense_selection = model.tag["expense"]
        assert expense_selection.sum(2024) == 60
        assert expense_selection.sum(2025) == 66

    def test_sum_empty_selection(self):
        """Test summing an empty selection."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        selection = model.select([])
        assert selection.sum(2024) == 0

    def test_sum_invalid_period(self):
        """Test that invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses"])
        with pytest.raises(KeyError, match="Period 2025 not found"):
            selection.sum(2025)

    def test_sum_with_negative_values(self):
        """Test summing items with negative values."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: -60})  # Negative
            adjustments = FixedLine(values={2024: -5})  # Negative

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses", "adjustments"])
        assert selection.sum(2024) == 35  # 100 + (-60) + (-5)


class TestLineItemSelectionTable:
    """Tests for selection.table() method."""

    def test_table_single_item(self):
        """Test generating a table for single selected item."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue"])
        table = selection.table()
        
        assert isinstance(table, Table)
        # Header + 1 item row + blank row + total row (with include_total_row=True by default)
        assert len(table.cells) == 4

    def test_table_multiple_items(self):
        """Test generating a table for multiple selected items."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses", "profit"])
        table = selection.table()
        
        assert isinstance(table, Table)
        # Header + 3 item rows + blank row + total row (with include_total_row=True by default)
        assert len(table.cells) == 6

    def test_table_preserves_order(self):
        """Test that table preserves selection order."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024])

        # Select in specific order
        selection = model.select(["profit", "revenue", "expenses"])
        table = selection.table()
        
        # Check order in table (skip header row, rows 1-3 are line items before total)
        assert table.cells[1][0].value == "profit"
        assert table.cells[2][0].value == "revenue"
        assert table.cells[3][0].value == "expenses"

    def test_table_with_include_name(self):
        """Test table with include_name parameter."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, label="Total Revenue")
            expenses = FixedLine(values={2024: 60}, label="Total Expenses")

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses"])
        
        # With name
        table_with_name = selection.table(include_name=True)
        assert isinstance(table_with_name, Table)
        
        # Without name (but with label)
        table_no_name = selection.table(include_name=False, include_label=True)
        assert isinstance(table_no_name, Table)

    def test_table_with_include_label(self):
        """Test table with include_label parameter."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, label="Total Revenue")
            expenses = FixedLine(values={2024: 60}, label="Total Expenses")

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses"])
        
        # With label
        table = selection.table(include_name=False, include_label=True)
        assert isinstance(table, Table)

    def test_table_empty_selection(self):
        """Test generating a table with empty selection."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        selection = model.select([])
        table = selection.table()
        
        assert isinstance(table, Table)
        # Only header row (no items, so no total row either)
        assert len(table.cells) == 1

    def test_table_values_match(self):
        """Test that table values match the line item values."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses"])
        table = selection.table()
        
        # Check values in table (skip header row, skip label column)
        # Row 1 is revenue
        assert table.cells[1][1].value == 100  # 2024
        assert table.cells[1][2].value == 110  # 2025
        
        # Row 2 is expenses
        assert table.cells[2][1].value == 60   # 2024
        assert table.cells[2][2].value == 66   # 2025

    def test_table_with_totals_default(self):
        """Test that table includes totals by default."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses"])
        table = selection.table()
        
        # Should have header + 2 items + blank + total = 5 rows
        assert len(table.cells) == 5
        
        # Check blank row
        assert table.cells[3][0].value == ""
        
        # Check total row
        total_row = table.cells[4]
        assert total_row[0].value == "Total"
        assert total_row[0].bold is True
        # Total for 2024: 100 + 60 = 160
        assert total_row[1].value == 160
        # Total for 2025: 110 + 66 = 176
        assert total_row[2].value == 176

    def test_table_without_totals(self):
        """Test generating table without totals."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FixedLine(values={2024: 60, 2025: 66})

        model = TestModel(periods=[2024, 2025])

        selection = model.select(["revenue", "expenses"])
        table = selection.table(include_total_row=False)
        
        # Should have header + 2 items only (no total row)
        assert len(table.cells) == 3
        
        # Verify no "Total" row
        assert all(row[0].value != "Total" for row in table.cells)
        
        # Verify no blank row before what would be total
        assert table.cells[2][0].value in ["revenue", "expenses"]

    def test_table_with_totals_explicit_true(self):
        """Test explicitly setting include_total_row=True."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})

        model = TestModel(periods=[2024])

        selection = model.select(["revenue", "expenses"])
        table = selection.table(include_total_row=True)
        
        # Should have header + 2 items + blank + total = 5 rows
        assert len(table.cells) == 5
        
        # Check total row
        total_row = table.cells[4]
        assert total_row[0].value == "Total"
        assert total_row[1].value == 160  # 100 + 60
