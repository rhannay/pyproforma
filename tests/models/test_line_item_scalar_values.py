"""Tests for LineItem scalar values (constants)."""

import pytest

from pyproforma import LineItem, Model


class TestLineItemScalarValues:
    """Test LineItem with scalar values instead of dicts."""

    def test_scalar_value_float(self):
        """Test creating a LineItem with a scalar float value."""
        item = LineItem(
            name="tax_rate",
            category="assumptions",
            values=0.21,
        )
        assert item.name == "tax_rate"
        assert item.values == 0.21
        assert item.formula is None

    def test_scalar_value_integer(self):
        """Test creating a LineItem with a scalar integer value."""
        item = LineItem(name="base_year", values=2020)
        assert item.values == 2020

    def test_scalar_value_in_model(self):
        """Test that scalar values work in a Model."""
        tax_rate = LineItem(name="tax_rate", values=0.21)
        revenue = LineItem(name="revenue", values={2020: 100, 2021: 110})

        model = Model(line_items=[tax_rate, revenue], years=[2020, 2021])

        # Scalar should have the same value for all years
        assert model.value("tax_rate", 2020) == 0.21
        assert model.value("tax_rate", 2021) == 0.21

    def test_scalar_value_in_formula(self):
        """Test using scalar value in formulas."""
        tax_rate = LineItem(name="tax_rate", values=0.21)
        ebit = LineItem(name="ebit", values={2020: 100})
        tax_expense = LineItem(
            name="tax_expense",
            formula="ebit * tax_rate",
        )

        model = Model(
            line_items=[tax_rate, ebit, tax_expense],
            years=[2020],
        )

        # Check that formula uses the scalar correctly
        assert model.value("tax_expense", 2020) == 21.0

    def test_scalar_value_multi_year(self):
        """Test scalar value used across multiple years in formulas."""
        inflation = LineItem(name="inflation", values=0.03)
        base_revenue = LineItem(
            name="revenue", values={2020: 1000, 2021: 1100, 2022: 1210}
        )
        adjusted_revenue = LineItem(
            name="adjusted_revenue",
            formula="revenue * (1 + inflation)",
        )

        model = Model(
            line_items=[inflation, base_revenue, adjusted_revenue],
            years=[2020, 2021, 2022],
        )

        # Verify scalar is used in calculations across years
        assert model.value("inflation", 2020) == 0.03
        assert model.value("inflation", 2021) == 0.03
        assert model.value("inflation", 2022) == 0.03
        assert model.value("adjusted_revenue", 2020) == 1030.0
        assert model.value("adjusted_revenue", 2021) == 1133.0

    def test_multiple_scalars_in_model(self):
        """Test multiple scalar values in a model."""
        tax_rate = LineItem(name="tax_rate", values=0.21)
        inflation = LineItem(name="inflation", values=0.03)
        discount_rate = LineItem(name="discount_rate", values=0.08)

        model = Model(
            line_items=[tax_rate, inflation, discount_rate],
            years=[2020, 2021],
        )

        # All scalars should maintain their values across years
        assert model.value("tax_rate", 2020) == 0.21
        assert model.value("inflation", 2020) == 0.03
        assert model.value("discount_rate", 2020) == 0.08
        assert model.value("tax_rate", 2021) == 0.21
        assert model.value("inflation", 2021) == 0.03
        assert model.value("discount_rate", 2021) == 0.08

    def test_scalar_with_category_total(self):
        """Test scalar value used with category_total formula."""
        inflation = LineItem(name="inflation", category="assumptions", values=0.03)
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

    def test_scalar_serialization(self):
        """Test that scalar values serialize correctly."""
        item = LineItem(name="tax_rate", values=0.21)
        item_dict = item.to_dict()
        assert item_dict["values"] == 0.21

    def test_scalar_deserialization(self):
        """Test that scalar values deserialize correctly."""
        item_dict = {
            "name": "tax_rate",
            "category": "assumptions",
            "values": 0.21,
        }
        item = LineItem.from_dict(item_dict)
        assert item.values == 0.21

    def test_dict_values_still_work(self):
        """Ensure dict values still work as before."""
        item = LineItem(
            name="revenue",
            values={2020: 100, 2021: 110},
        )
        model = Model(line_items=[item], years=[2020, 2021])
        assert model.value("revenue", 2020) == 100
        assert model.value("revenue", 2021) == 110

    def test_mixed_scalar_and_dict_values(self):
        """Test model with both scalar and dict values."""
        tax_rate = LineItem(name="tax_rate", values=0.21)
        revenue = LineItem(name="revenue", values={2020: 100, 2021: 110})
        tax = LineItem(name="tax", formula="revenue * tax_rate")

        model = Model(
            line_items=[tax_rate, revenue, tax],
            years=[2020, 2021],
        )

        assert model.value("tax_rate", 2020) == 0.21
        assert model.value("tax_rate", 2021) == 0.21
        assert model.value("tax", 2020) == 21.0
        assert abs(model.value("tax", 2021) - 23.1) < 0.001  # Handle float precision
