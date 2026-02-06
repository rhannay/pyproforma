"""Tests for LineItem constant feature."""

import pytest

from pyproforma import LineItem, Model


class TestLineItemConstant:
    """Test LineItem constant parameter."""

    def test_constant_init(self):
        """Test creating a LineItem with constant value."""
        item = LineItem(
            name="inflation_rate",
            category="assumptions",
            constant=0.03,
        )
        assert item.name == "inflation_rate"
        assert item.constant == 0.03
        assert item.values is None
        assert item.formula is None

    def test_constant_with_label(self):
        """Test creating a constant LineItem with label."""
        item = LineItem(
            name="inflation_rate",
            label="Annual Inflation Rate",
            category="assumptions",
            constant=0.03,
        )
        assert item.label == "Annual Inflation Rate"
        assert item.constant == 0.03

    def test_constant_integer(self):
        """Test creating a constant LineItem with integer value."""
        item = LineItem(name="base_year", constant=2020)
        assert item.constant == 2020

    def test_constant_float(self):
        """Test creating a constant LineItem with float value."""
        item = LineItem(name="rate", constant=0.025)
        assert item.constant == 0.025

    def test_constant_boolean(self):
        """Test creating a constant LineItem with boolean value."""
        item = LineItem(name="flag", constant=True)
        assert item.constant is True

    def test_constant_cannot_have_values(self):
        """Test that constant cannot be used with values."""
        with pytest.raises(ValueError) as exc_info:
            LineItem(
                name="invalid",
                constant=0.03,
                values={2020: 100},
            )
        assert "cannot have both 'constant' and 'values'" in str(exc_info.value)

    def test_constant_cannot_have_formula(self):
        """Test that constant cannot be used with formula."""
        with pytest.raises(ValueError) as exc_info:
            LineItem(
                name="invalid",
                constant=0.03,
                formula="revenue * 0.1",
            )
        assert "cannot have both 'constant' and 'formula'" in str(exc_info.value)

    def test_constant_must_be_numeric(self):
        """Test that constant must be numeric."""
        with pytest.raises(TypeError) as exc_info:
            LineItem(name="invalid", constant="0.03")
        assert "constant must be numeric" in str(exc_info.value)

    def test_constant_serialization(self):
        """Test that constant is included in to_dict."""
        item = LineItem(name="inflation", constant=0.03)
        item_dict = item.to_dict()
        assert item_dict["constant"] == 0.03
        assert item_dict["values"] is None
        assert item_dict["formula"] is None

    def test_constant_deserialization(self):
        """Test that constant is restored from from_dict."""
        item_dict = {
            "name": "inflation",
            "category": "assumptions",
            "constant": 0.03,
        }
        item = LineItem.from_dict(item_dict)
        assert item.constant == 0.03
        assert item.values is None
        assert item.formula is None


class TestConstantInModel:
    """Test constant LineItems in Model."""

    def test_constant_in_model(self):
        """Test that constant LineItem works in a Model."""
        inflation = LineItem(name="inflation", constant=0.03)
        revenue = LineItem(name="revenue", values={2020: 100, 2021: 110})

        model = Model(line_items=[inflation, revenue], years=[2020, 2021])

        # Constant should have the same value for all years
        assert model.value("inflation", 2020) == 0.03
        assert model.value("inflation", 2021) == 0.03

    def test_constant_in_formula(self):
        """Test using constant in formulas."""
        inflation = LineItem(name="inflation", constant=0.03)
        base_revenue = LineItem(name="base_revenue", values={2020: 100})
        adjusted_revenue = LineItem(
            name="adjusted_revenue",
            formula="base_revenue * (1 + inflation)",
        )

        model = Model(
            line_items=[inflation, base_revenue, adjusted_revenue],
            years=[2020],
        )

        # Check that formula uses the constant correctly
        assert model.value("adjusted_revenue", 2020) == 103.0

    def test_constant_in_multi_year_formula(self):
        """Test constant used across multiple years in formulas."""
        growth_rate = LineItem(name="growth_rate", constant=0.1)
        revenue_2020 = LineItem(
            name="revenue", values={2020: 1000, 2021: 1100, 2022: 1210}
        )

        # Add formula-based line item that uses the constant
        revenue_adjusted = LineItem(
            name="revenue_adjusted",
            formula="revenue * (1 + growth_rate)",
        )

        model_with_growth = Model(
            line_items=[growth_rate, revenue_2020, revenue_adjusted],
            years=[2020, 2021, 2022],
        )

        # Verify constant is used in calculations across years
        assert model_with_growth.value("growth_rate", 2020) == 0.1
        assert model_with_growth.value("growth_rate", 2021) == 0.1
        assert model_with_growth.value("growth_rate", 2022) == 0.1
        assert model_with_growth.value("revenue_adjusted", 2020) == 1100.0
        assert model_with_growth.value("revenue_adjusted", 2021) == 1210.0

    def test_multiple_constants_in_model(self):
        """Test multiple constants in a model."""
        inflation = LineItem(name="inflation", constant=0.03)
        tax_rate = LineItem(name="tax_rate", constant=0.21)
        discount_rate = LineItem(name="discount_rate", constant=0.08)

        model = Model(
            line_items=[inflation, tax_rate, discount_rate],
            years=[2020, 2021],
        )

        # All constants should maintain their values across years
        assert model.value("inflation", 2020) == 0.03
        assert model.value("tax_rate", 2020) == 0.21
        assert model.value("discount_rate", 2020) == 0.08
        assert model.value("inflation", 2021) == 0.03
        assert model.value("tax_rate", 2021) == 0.21
        assert model.value("discount_rate", 2021) == 0.08

    def test_constant_with_category_total(self):
        """Test constant used with category_total formula."""
        inflation = LineItem(name="inflation", category="assumptions", constant=0.03)
        revenue = LineItem(name="revenue", category="income", values={2020: 100})
        total_income = LineItem(
            name="total_income",
            category="totals",
            formula="category_total:income",
        )
        adjusted_total = LineItem(
            name="adjusted_total",
            category="adjusted",
            formula="total_income * (1 + inflation)",
        )

        model = Model(
            line_items=[inflation, revenue, total_income, adjusted_total],
            years=[2020],
        )

        assert model.value("adjusted_total", 2020) == 103.0
