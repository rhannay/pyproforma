"""
Tests for LineItemResult class and model['item'] access in v2.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, Format, ProformaModel, ScalarLine
from pyproforma.results.line_item_result import LineItemResult


class TestModelGetItemAccess:
    """Tests for model['item'] dictionary-style access."""

    def test_getitem_returns_line_item_result(self):
        """Test that model['item'] returns a LineItemResult object."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        result = model["revenue"]

        assert isinstance(result, LineItemResult)
        assert result.name == "revenue"

    def test_getitem_with_nonexistent_item(self):
        """Test that accessing a non-existent item raises AttributeError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(AttributeError, match="Item 'nonexistent' not found"):
            model["nonexistent"]

    def test_getitem_with_non_string_key(self):
        """Test that using non-string key raises TypeError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(TypeError, match="Expected string"):
            model[123]

    def test_getitem_multiple_items(self):
        """Test accessing multiple items via model['item']."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(
                formula=lambda li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        revenue_result = model["revenue"]
        expenses_result = model["expenses"]
        profit_result = model["profit"]

        assert isinstance(revenue_result, LineItemResult)
        assert isinstance(expenses_result, LineItemResult)
        assert isinstance(profit_result, LineItemResult)

        assert revenue_result.name == "revenue"
        assert expenses_result.name == "expenses"
        assert profit_result.name == "profit"


class TestLineItemResultClass:
    """Tests for LineItemResult class functionality."""

    def test_initialization(self):
        """Test LineItemResult initialization."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = LineItemResult(model, "revenue")

        assert result.name == "revenue"
        assert result._model is model

    def test_initialization_with_invalid_name(self):
        """Test that initializing with invalid name raises AttributeError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])

        with pytest.raises(AttributeError, match="Line item 'invalid' not found"):
            LineItemResult(model, "invalid")

    def test_repr(self):
        """Test LineItemResult __repr__ method."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert repr(result) == "LineItemResult(name='revenue')"

    def test_str(self):
        """Test LineItemResult __str__ method."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        result = model["revenue"]

        str_repr = str(result)
        assert "revenue" in str_repr
        assert "2024" in str_repr
        assert "100" in str_repr

    def test_getitem_single_period(self):
        """Test accessing value via result[period] for single period."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert result[2024] == 100

    def test_getitem_multiple_periods(self):
        """Test accessing values via result[period] for multiple periods."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel(periods=[2024, 2025, 2026])
        result = model["revenue"]

        assert result[2024] == 100
        assert result[2025] == 110
        assert result[2026] == 121

    def test_getitem_invalid_period(self):
        """Test that accessing invalid period raises KeyError."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        with pytest.raises(KeyError):
            result[2025]

    def test_name_property(self):
        """Test the name property."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert result.name == "revenue"

    def test_label_property_with_label(self):
        """Test the label property when label is set."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, label="Total Revenue")
            expenses = FormulaLine(
                formula=lambda li, t: li.revenue[t] * 0.6, label="Operating Expenses"
            )

        model = TestModel(periods=[2024])

        revenue_result = model["revenue"]
        expenses_result = model["expenses"]

        assert revenue_result.label == "Total Revenue"
        assert expenses_result.label == "Operating Expenses"

    def test_label_property_without_label(self):
        """Test the label property when label is not set."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert result.label is None

    def test_values_property(self):
        """Test the values property returns all period values."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})

        model = TestModel(periods=[2024, 2025, 2026])
        result = model["revenue"]

        values = result.values
        assert isinstance(values, dict)
        assert values == {2024: 100, 2025: 110, 2026: 121}

    def test_value_method(self):
        """Test the value() method."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        result = model["revenue"]

        assert result.value(2024) == 100
        assert result.value(2025) == 110

    def test_value_method_invalid_period(self):
        """Test that value() method raises KeyError for invalid period."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        with pytest.raises(KeyError):
            result.value(2025)


class TestLineItemResultWithFormulas:
    """Tests for LineItemResult with calculated values."""

    def test_formula_line_access(self):
        """Test accessing calculated formula line values."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)

        model = TestModel(periods=[2024])
        result = model["expenses"]

        assert result[2024] == 60.0

    def test_complex_formula_chain(self):
        """Test accessing values from complex formula chains."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
            profit = FormulaLine(
                formula=lambda li, t: li.revenue[t] - li.expenses[t]
            )

        model = TestModel(periods=[2024, 2025])

        revenue_result = model["revenue"]
        expenses_result = model["expenses"]
        profit_result = model["profit"]

        assert revenue_result[2024] == 100
        assert expenses_result[2024] == 60.0
        assert profit_result[2024] == 40.0

        assert revenue_result[2025] == 110
        assert expenses_result[2025] == 66.0
        assert profit_result[2025] == 44.0

    def test_formula_with_assumptions(self):
        """Test accessing formula values that use assumptions."""

        class TestModel(ProformaModel):
            expense_ratio = ScalarLine(value=0.6)
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(
                formula=lambda li, t: li.revenue[t] * li.expense_ratio
            )

        model = TestModel(periods=[2024])
        result = model["expenses"]

        assert result[2024] == 60.0
        assert result.values == {2024: 60.0}


class TestLineItemResultFormattedValue:
    """Tests for LineItemResult.formatted_value()."""

    def test_formatted_value_currency(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 1_000_000}, value_format=Format.CURRENCY_NO_DECIMALS)

        model = TestModel(periods=[2024])
        assert model["revenue"].formatted_value(2024) == "$1,000,000"

    def test_formatted_value_percent(self):
        class TestModel(ProformaModel):
            margin = FixedLine(values={2024: 0.354}, value_format=Format.PERCENT_ONE_DECIMAL)

        model = TestModel(periods=[2024])
        assert model["margin"].formatted_value(2024) == "35.4%"

    def test_formatted_value_default_format(self):
        class TestModel(ProformaModel):
            count = FixedLine(values={2024: 42})

        model = TestModel(periods=[2024])
        assert model["count"].formatted_value(2024) == "42"

    def test_formatted_value_raises_on_invalid_period(self):
        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        with pytest.raises(KeyError):
            model["revenue"].formatted_value(2099)



class TestLineItemResultAggregations:
    """Tests for min, max, first, latest and their formatted variants."""

    def _model(self):
        class M(ProformaModel):
            revenue = FixedLine(
                values={2024: 100_000, 2025: 110_000, 2026: 80_000},
                value_format=Format.CURRENCY_NO_DECIMALS,
            )
        return M(periods=[2024, 2025, 2026])

    def test_min(self):
        assert self._model()["revenue"].min() == 80_000

    def test_max(self):
        assert self._model()["revenue"].max() == 110_000

    def test_first(self):
        assert self._model()["revenue"].first() == 100_000

    def test_latest(self):
        assert self._model()["revenue"].latest() == 80_000

    def test_min_returns_none_when_no_periods(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        assert M()["revenue"].min() is None

    def test_max_returns_none_when_no_periods(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        assert M()["revenue"].max() is None

    def test_first_returns_none_when_no_periods(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        assert M()["revenue"].first() is None

    def test_latest_returns_none_when_no_periods(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        assert M()["revenue"].latest() is None

    def test_formatted_min(self):
        assert self._model()["revenue"].formatted_min() == "$80,000"

    def test_formatted_max(self):
        assert self._model()["revenue"].formatted_max() == "$110,000"

    def test_formatted_first(self):
        assert self._model()["revenue"].formatted_first() == "$100,000"

    def test_formatted_latest(self):
        assert self._model()["revenue"].formatted_latest() == "$80,000"

    def test_formatted_min_override_format(self):
        assert self._model()["revenue"].formatted_min(Format.THOUSANDS_K) == "80.0K"

    def test_formatted_returns_empty_string_when_none(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        assert M()["revenue"].formatted_min() == ""
