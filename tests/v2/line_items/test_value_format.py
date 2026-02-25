"""
Tests for value_format functionality in v2 line items.
"""

import pytest

from pyproforma.table import Format, NumberFormatSpec
from pyproforma.v2 import (
    FixedLine,
    FormulaLine,
    ProformaModel,
    create_debt_lines,
)


class TestFixedLineValueFormat:
    """Tests for value_format in FixedLine."""

    def test_fixed_line_default_value_format(self):
        """Test that FixedLine has default value_format of 'no_decimals'."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        model = TestModel(periods=[2024, 2025])
        result = model["revenue"]

        assert result.value_format is not None
        assert result.value_format == Format.NO_DECIMALS

    def test_fixed_line_with_string_format(self):
        """Test FixedLine with string format specification."""

        class TestModel(ProformaModel):
            tax_rate = FixedLine(
                values={2024: 0.21, 2025: 0.22}, value_format="percent"
            )

        model = TestModel(periods=[2024, 2025])
        result = model["tax_rate"]

        assert result.value_format == Format.PERCENT
        assert result.value_format.suffix == "%"
        assert result.value_format.multiplier == 100

    def test_fixed_line_with_format_constant(self):
        """Test FixedLine with Format constant."""

        class TestModel(ProformaModel):
            price = FixedLine(
                values={2024: 1234.56, 2025: 1345.67}, value_format=Format.CURRENCY
            )

        model = TestModel(periods=[2024, 2025])
        result = model["price"]

        assert result.value_format == Format.CURRENCY
        assert result.value_format.prefix == "$"
        assert result.value_format.decimals == 2

    def test_fixed_line_with_number_format_spec(self):
        """Test FixedLine with NumberFormatSpec instance."""

        custom_format = NumberFormatSpec(
            decimals=3, thousands=False, prefix="€", suffix=""
        )

        class TestModel(ProformaModel):
            amount = FixedLine(values={2024: 1000}, value_format=custom_format)

        model = TestModel(periods=[2024])
        result = model["amount"]

        assert result.value_format == custom_format
        assert result.value_format.prefix == "€"
        assert result.value_format.decimals == 3

    def test_fixed_line_with_dict_format(self):
        """Test FixedLine with dict format specification."""

        class TestModel(ProformaModel):
            amount = FixedLine(
                values={2024: 1000},
                value_format={"decimals": 1, "prefix": "£", "thousands": True},
            )

        model = TestModel(periods=[2024])
        result = model["amount"]

        assert result.value_format.decimals == 1
        assert result.value_format.prefix == "£"
        assert result.value_format.thousands is True


class TestFormulaLineValueFormat:
    """Tests for value_format in FormulaLine."""

    def test_formula_line_default_value_format(self):
        """Test that FormulaLine has default value_format of 'no_decimals'."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            profit = FormulaLine(formula=lambda a, li, t: li.revenue[t] * 0.1)

        model = TestModel(periods=[2024])
        result = model["profit"]

        assert result.value_format is not None
        assert result.value_format == Format.NO_DECIMALS

    def test_formula_line_with_string_format(self):
        """Test FormulaLine with string format specification."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            growth = FormulaLine(
                formula=lambda a, li, t: (
                    (li.revenue[t] - li.revenue[t - 1]) / li.revenue[t - 1]
                ),
                values={2024: 0.0},  # No prior value for first period
                value_format="percent_two_decimals",
            )

        model = TestModel(periods=[2024, 2025])
        result = model["growth"]

        assert result.value_format == Format.PERCENT_TWO_DECIMALS
        assert result.value_format.suffix == "%"
        assert result.value_format.decimals == 2

    def test_formula_line_with_format_constant(self):
        """Test FormulaLine with Format constant."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 1000})
            cost = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * 0.6,
                value_format=Format.CURRENCY_NO_DECIMALS,
            )

        model = TestModel(periods=[2024])
        result = model["cost"]

        assert result.value_format == Format.CURRENCY_NO_DECIMALS
        assert result.value_format.prefix == "$"
        assert result.value_format.decimals == 0


class TestDebtLineValueFormat:
    """Tests for value_format in debt line items."""

    def test_debt_lines_default_value_format(self):
        """Test that debt lines have default value_format of 'no_decimals'."""

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0})
            principal, interest = create_debt_lines(
                par_amounts_line_item="bond_proceeds",
                interest_rate=0.05,
                term=10,
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026])
        principal_result = model["principal_payment"]
        interest_result = model["interest_expense"]

        assert principal_result.value_format is not None
        assert interest_result.value_format is not None
        assert principal_result.value_format == Format.NO_DECIMALS
        assert interest_result.value_format == Format.NO_DECIMALS

    def test_debt_lines_with_custom_formats(self):
        """Test debt lines with custom value formats."""

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0})
            principal, interest = create_debt_lines(
                par_amounts_line_item="bond_proceeds",
                interest_rate=0.05,
                term=10,
                principal_value_format="currency_no_decimals",
                interest_value_format=Format.CURRENCY,
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026])
        principal_result = model["principal_payment"]
        interest_result = model["interest_expense"]

        assert principal_result.value_format == Format.CURRENCY_NO_DECIMALS
        assert interest_result.value_format == Format.CURRENCY
        assert principal_result.value_format.decimals == 0
        assert interest_result.value_format.decimals == 2

    def test_debt_lines_with_separate_formats(self):
        """Test that principal and interest can have different formats."""

        class TestModel(ProformaModel):
            bond_proceeds = FixedLine(values={2024: 1_000_000, 2025: 0, 2026: 0})
            principal, interest = create_debt_lines(
                par_amounts_line_item="bond_proceeds",
                interest_rate=0.05,
                term=10,
                principal_value_format="no_decimals",
                interest_value_format="two_decimals",
            )
            principal_payment = principal
            interest_expense = interest

        model = TestModel(periods=[2024, 2025, 2026])
        principal_result = model["principal_payment"]
        interest_result = model["interest_expense"]

        assert principal_result.value_format != interest_result.value_format
        assert principal_result.value_format.decimals == 0
        assert interest_result.value_format.decimals == 2


class TestValueFormatInheritance:
    """Tests for value_format inheritance and defaults."""

    def test_multiple_line_items_with_different_formats(self):
        """Test that different line items can have different formats."""

        class TestModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 1_000_000}, value_format="currency_no_decimals"
            )
            growth_rate = FixedLine(values={2024: 0.15}, value_format="percent")
            margin = FormulaLine(
                formula=lambda a, li, t: 0.25, value_format="percent_two_decimals"
            )
            profit = FormulaLine(
                formula=lambda a, li, t: li.revenue[t] * li.margin[t],
                value_format=Format.CURRENCY,
            )

        model = TestModel(periods=[2024])

        assert model["revenue"].value_format == Format.CURRENCY_NO_DECIMALS
        assert model["growth_rate"].value_format == Format.PERCENT
        assert model["margin"].value_format == Format.PERCENT_TWO_DECIMALS
        assert model["profit"].value_format == Format.CURRENCY

    def test_none_value_format_uses_default(self):
        """Test that None value_format uses the default."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, value_format=None)

        model = TestModel(periods=[2024])
        result = model["revenue"]

        # None should result in default Format.NO_DECIMALS
        assert result.value_format == Format.NO_DECIMALS


class TestValueFormatPropertyAccess:
    """Tests for accessing value_format property through LineItemResult."""

    def test_value_format_property_accessible(self):
        """Test that value_format is accessible through result object."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100}, value_format="currency")

        model = TestModel(periods=[2024])
        result = model["revenue"]

        # Direct property access
        assert hasattr(result, "value_format")
        assert result.value_format is not None

    def test_value_format_property_read_only(self):
        """Test that value_format property is read-only."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        model = TestModel(periods=[2024])
        result = model["revenue"]

        # Attempting to set should not work (it's read-only)
        with pytest.raises(AttributeError):
            result.value_format = Format.CURRENCY

    def test_value_format_with_label_and_tags(self):
        """Test that value_format works alongside label and tags."""

        class TestModel(ProformaModel):
            revenue = FixedLine(
                values={2024: 100},
                label="Total Revenue",
                tags=["income", "operational"],
                value_format="currency",
            )

        model = TestModel(periods=[2024])
        result = model["revenue"]

        assert result.label == "Total Revenue"
        assert result.tags == ["income", "operational"]
        assert result.value_format == Format.CURRENCY
