"""
Tests for AssumptionResult class and model['assumption'] access in v2.
"""

import pytest

from pyproforma import Assumption, FixedLine, FormulaLine, InputAssumption, ProformaModel
from pyproforma.assumption_result import AssumptionResult
from pyproforma.table import Format, NumberFormatSpec


class TestModelGetItemAccessForAssumptions:
    """Tests for model['assumption'] dictionary-style access."""

    def test_getitem_returns_assumption_result(self):
        """Test that model['assumption'] returns an AssumptionResult object."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert isinstance(result, AssumptionResult)
        assert result.name == "inflation_rate"
        assert result.value == 0.03

    def test_getitem_with_nonexistent_assumption(self):
        """Test that accessing a non-existent assumption raises AttributeError."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])

        with pytest.raises(AttributeError, match="Item 'nonexistent' not found"):
            model["nonexistent"]

    def test_getitem_distinguishes_assumptions_and_line_items(self):
        """Test that model['x'] returns the right type for assumptions vs line items."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        from pyproforma.line_items.line_item_result import LineItemResult

        tax_result = model["tax_rate"]
        revenue_result = model["revenue"]

        assert isinstance(tax_result, AssumptionResult)
        assert isinstance(revenue_result, LineItemResult)

    def test_getitem_multiple_assumptions(self):
        """Test accessing multiple assumptions via model['assumption']."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)
            tax_rate = Assumption(value=0.21)
            growth_rate = Assumption(value=0.15)

        model = TestModel(periods=[2024])

        inflation_result = model["inflation_rate"]
        tax_result = model["tax_rate"]
        growth_result = model["growth_rate"]

        assert isinstance(inflation_result, AssumptionResult)
        assert isinstance(tax_result, AssumptionResult)
        assert isinstance(growth_result, AssumptionResult)

        assert inflation_result.value == 0.03
        assert tax_result.value == 0.21
        assert growth_result.value == 0.15


class TestAssumptionResultClass:
    """Tests for AssumptionResult class functionality."""

    def test_initialization(self):
        """Test AssumptionResult initialization."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = AssumptionResult(model, "inflation_rate")

        assert result.name == "inflation_rate"
        assert result.value == 0.03
        assert result._model is model

    def test_initialization_with_invalid_name(self):
        """Test that initializing with invalid name raises AttributeError."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])

        with pytest.raises(AttributeError, match="Assumption 'invalid' not found"):
            AssumptionResult(model, "invalid")

    def test_repr(self):
        """Test AssumptionResult __repr__ method."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert repr(result) == "AssumptionResult(name='inflation_rate', value=0.03)"

    def test_str(self):
        """Test AssumptionResult __str__ method."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert str(result) == "inflation_rate: 0.03"

    def test_float_conversion(self):
        """Test converting AssumptionResult to float."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert float(result) == 0.03
        assert isinstance(float(result), float)

    def test_name_property(self):
        """Test the name property."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert result.name == "inflation_rate"

    def test_value_property(self):
        """Test the value property."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024])

        inflation_result = model["inflation_rate"]
        tax_result = model["tax_rate"]

        assert inflation_result.value == 0.03
        assert tax_result.value == 0.21

    def test_label_property_with_label(self):
        """Test the label property when label is set."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03, label="Annual Inflation Rate")
            tax_rate = Assumption(value=0.21, label="Corporate Tax Rate")

        model = TestModel(periods=[2024])

        inflation_result = model["inflation_rate"]
        tax_result = model["tax_rate"]

        assert inflation_result.label == "Annual Inflation Rate"
        assert tax_result.label == "Corporate Tax Rate"

    def test_label_property_without_label(self):
        """Test the label property when label is not set."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert result.label is None

    def test_value_format_property_default(self):
        """Test that value_format defaults to NO_DECIMALS."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03)

        model = TestModel(periods=[2024])
        result = model["inflation_rate"]

        assert result.value_format == Format.NO_DECIMALS

    def test_value_format_property_with_string(self):
        """Test value_format set via string name."""

        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21, value_format="percent")

        model = TestModel(periods=[2024])
        result = model["tax_rate"]

        assert result.value_format == Format.PERCENT

    def test_value_format_property_with_format_constant(self):
        """Test value_format set via Format constant."""

        class TestModel(ProformaModel):
            revenue = Assumption(value=1_000_000, value_format=Format.CURRENCY)

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert result.value_format == Format.CURRENCY

    def test_value_format_property_with_number_format_spec(self):
        """Test value_format set via NumberFormatSpec instance."""

        custom_fmt = NumberFormatSpec(decimals=3, thousands=True)

        class TestModel(ProformaModel):
            rate = Assumption(value=0.005, value_format=custom_fmt)

        model = TestModel(periods=[2024])
        result = model["rate"]

        assert result.value_format == custom_fmt

    def test_value_format_on_input_assumption(self):
        """Test that value_format on InputAssumption is surfaced via AssumptionResult."""

        class TestModel(ProformaModel):
            tax_rate = InputAssumption(default=0.21, value_format=Format.PERCENT)

        model = TestModel(periods=[2024])
        result = model["tax_rate"]

        assert result.value_format == Format.PERCENT


class TestAssumptionResultFormattedValue:
    """Tests for AssumptionResult.formatted_value property."""

    def test_formatted_value_percent(self):
        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21, value_format=Format.PERCENT)

        model = TestModel(periods=[2024])
        assert model["tax_rate"].formatted_value == "21%"

    def test_formatted_value_percent_one_decimal(self):
        class TestModel(ProformaModel):
            cogs_rate = Assumption(value=0.354, value_format=Format.PERCENT_ONE_DECIMAL)

        model = TestModel(periods=[2024])
        assert model["cogs_rate"].formatted_value == "35.4%"

    def test_formatted_value_default_format(self):
        class TestModel(ProformaModel):
            count = Assumption(value=42)

        model = TestModel(periods=[2024])
        assert model["count"].formatted_value == "42"

    def test_formatted_value_input_assumption(self):
        class TestModel(ProformaModel):
            growth = InputAssumption(default=0.05, value_format=Format.PERCENT_ONE_DECIMAL)

        model = TestModel(periods=[2024])
        assert model["growth"].formatted_value == "5.0%"


class TestAssumptionResultGetItem:
    """Tests for AssumptionResult.__getitem__ (period-indexed access)."""

    def test_getitem_returns_scalar_value(self):
        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024, 2025])
        result = model["tax_rate"]

        assert result[2024] == 0.21
        assert result[2025] == 0.21

    def test_getitem_raises_on_invalid_period(self):
        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024, 2025])
        result = model["tax_rate"]

        with pytest.raises(KeyError):
            result[2055]

    def test_getitem_works_for_input_assumption(self):
        class TestModel(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        model = TestModel(periods=[2024, 2025])
        result = model["tax_rate"]

        assert result[2024] == 0.21
        assert result[2025] == 0.21

    def test_getitem_input_assumption_raises_on_invalid_period(self):
        class TestModel(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        model = TestModel(periods=[2024])
        result = model["tax_rate"]

        with pytest.raises(KeyError):
            result[2099]


class TestAssumptionResultIsInput:
    """Tests for AssumptionResult.is_input()."""

    def test_is_input_true_for_assumption(self):
        class TestModel(ProformaModel):
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024, 2025])
        result = model["tax_rate"]

        assert result.is_input(2024) is True
        assert result.is_input(2025) is True

    def test_is_input_true_for_input_assumption(self):
        class TestModel(ProformaModel):
            tax_rate = InputAssumption(default=0.21)

        model = TestModel(periods=[2024])
        result = model["tax_rate"]

        assert result.is_input(2024) is True


class TestAssumptionResultWithModel:
    """Tests for AssumptionResult in realistic model contexts."""

    def test_assumption_in_formula_context(self):
        """Test accessing assumption used in formulas."""

        class TestModel(ProformaModel):
            expense_ratio = Assumption(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(
                formula=lambda li, t: li.revenue[t] * li.expense_ratio
            )

        model = TestModel(periods=[2024])

        expense_ratio_result = model["expense_ratio"]

        assert expense_ratio_result.value == 0.6
        assert float(expense_ratio_result) == 0.6
        assert expense_ratio_result.name == "expense_ratio"

    def test_multiple_assumptions_and_line_items(self):
        """Test model with mix of assumptions and line items."""

        class TestModel(ProformaModel):
            inflation_rate = Assumption(value=0.03, label="Inflation Rate")
            tax_rate = Assumption(value=0.21, label="Tax Rate")
            revenue = FixedLine(values={2024: 100}, label="Revenue")
            expenses = FixedLine(values={2024: 60}, label="Expenses")

        model = TestModel(periods=[2024])

        # Access all via dictionary syntax
        inflation = model["inflation_rate"]
        tax = model["tax_rate"]
        revenue = model["revenue"]
        expenses = model["expenses"]

        # Verify types
        assert isinstance(inflation, AssumptionResult)
        assert isinstance(tax, AssumptionResult)

        from pyproforma.line_items.line_item_result import LineItemResult

        assert isinstance(revenue, LineItemResult)
        assert isinstance(expenses, LineItemResult)

        # Verify values
        assert inflation.value == 0.03
        assert tax.value == 0.21
        assert revenue[2024] == 100
        assert expenses[2024] == 60

        # Verify labels
        assert inflation.label == "Inflation Rate"
        assert tax.label == "Tax Rate"
        assert revenue.label == "Revenue"
        assert expenses.label == "Expenses"
