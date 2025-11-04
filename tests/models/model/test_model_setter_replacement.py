"""Tests for replacing existing line items using model['item'] = value syntax."""

import pytest

from pyproforma import Model
from pyproforma.models.line_item import LineItem


class TestReplaceWithPrimitiveValues:
    """Test replacing existing line items with primitive values (int, float)."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_formula_with_int_constant(self, model_with_line_item):
        """Test replacing a formula line item with an integer constant."""
        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000
        initial_item = model_with_line_item._line_item_definition("revenue")
        assert initial_item.formula == "1000"
        assert initial_item.category == "income"
        assert initial_item.label == "Total Revenue"
        assert initial_item.value_format == "currency"

        # Replace with integer constant
        model_with_line_item["revenue"] = 2000

        # Verify replacement
        assert model_with_line_item.value("revenue", 2023) == 2000.0
        assert model_with_line_item.value("revenue", 2024) == 2000.0
        assert model_with_line_item.value("revenue", 2025) == 2000.0

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values == {2023: 2000.0, 2024: 2000.0, 2025: 2000.0}

    def test_replace_values_with_float_constant(self, model_with_line_item):
        """Test replacing a values line item with a float constant."""
        # Set up a line item with values
        model_with_line_item["margin"] = LineItem(
            name="margin",
            category="ratios",
            label="Profit Margin",
            values={2023: 0.1, 2024: 0.12, 2025: 0.15},
            value_format="percent",
        )

        # Verify initial state
        assert model_with_line_item.value("margin", 2023) == 0.1
        assert model_with_line_item.value("margin", 2024) == 0.12

        # Replace with float constant
        model_with_line_item["margin"] = 0.2

        # Verify replacement
        assert model_with_line_item.value("margin", 2023) == 0.2
        assert model_with_line_item.value("margin", 2024) == 0.2
        assert model_with_line_item.value("margin", 2025) == 0.2

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("margin")
        assert updated_item.category == "ratios"  # Preserved
        assert updated_item.label == "Profit Margin"  # Preserved
        assert updated_item.value_format == "percent"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values == {2023: 0.2, 2024: 0.2, 2025: 0.2}


class TestReplaceWithList:
    """Test replacing existing line items with list values."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_formula_with_list(self, model_with_line_item):
        """Test replacing a formula line item with list values."""
        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000

        # Replace with list
        model_with_line_item["revenue"] = [2000, 2200, 2400]

        # Verify replacement
        assert model_with_line_item.value("revenue", 2023) == 2000.0
        assert model_with_line_item.value("revenue", 2024) == 2200.0
        assert model_with_line_item.value("revenue", 2025) == 2400.0

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values == {2023: 2000.0, 2024: 2200.0, 2025: 2400.0}


class TestReplaceWithFormula:
    """Test replacing existing line items with formula strings."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with existing line items."""
        model = Model(years=[2023, 2024, 2025])
        model["base"] = 1000
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            values={2023: 1000, 2024: 1100, 2025: 1200},
            value_format="currency",
        )
        return model

    def test_replace_values_with_formula(self, model_with_line_item):
        """Test replacing a values line item with a formula."""
        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000
        assert model_with_line_item.value("revenue", 2024) == 1100

        initial_item = model_with_line_item._line_item_definition("revenue")
        assert initial_item.values == {2023: 1000, 2024: 1100, 2025: 1200}
        assert initial_item.formula is None

        # Replace with formula
        model_with_line_item["revenue"] = "base * 2"

        # Verify replacement
        assert model_with_line_item.value("revenue", 2023) == 2000.0
        assert model_with_line_item.value("revenue", 2024) == 2000.0
        assert model_with_line_item.value("revenue", 2025) == 2000.0

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula == "base * 2"  # Updated
        assert updated_item.values is None  # Cleared

    def test_replace_formula_with_new_formula(self, model_with_line_item):
        """Test replacing a formula with another formula."""
        # Set up with initial formula that references revenue (which has values)
        # Note: formulas can reference line items with values, not just other formulas
        model_with_line_item["profit"] = LineItem(
            name="profit",
            category="income",
            label="Net Profit",
            formula="revenue * 0.1",
            value_format="currency",
        )

        # Verify initial state (revenue=1000 * 0.1)
        assert model_with_line_item.value("profit", 2023) == 100.0

        # Replace with new formula
        model_with_line_item["profit"] = "revenue * 0.2"

        # Verify replacement
        assert model_with_line_item.value("profit", 2023) == 200.0  # 1000 * 0.2

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("profit")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Net Profit"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula == "revenue * 0.2"  # Updated
        assert updated_item.values is None  # Still None


class TestReplaceWithValuesDict:
    """Test replacing existing line items with values dictionaries."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_formula_with_values_dict(self, model_with_line_item):
        """Test replacing a formula line item with a values dictionary."""
        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000

        # Replace with values dictionary
        model_with_line_item["revenue"] = {2023: 1500, 2024: 1650, 2025: 1800}

        # Verify replacement
        assert model_with_line_item.value("revenue", 2023) == 1500
        assert model_with_line_item.value("revenue", 2024) == 1650
        assert model_with_line_item.value("revenue", 2025) == 1800

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values == {2023: 1500, 2024: 1650, 2025: 1800}


class TestReplaceWithPandasSeries:
    """Test replacing existing line items with pandas Series."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_formula_with_series(self, model_with_line_item):
        """Test replacing a formula line item with a pandas Series."""
        pd = pytest.importorskip("pandas")

        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000

        # Replace with pandas Series
        series = pd.Series({2023: 3000.0, 2024: 3300.0, 2025: 3600.0})
        model_with_line_item["revenue"] = series

        # Verify replacement
        assert model_with_line_item.value("revenue", 2023) == 3000.0
        assert model_with_line_item.value("revenue", 2024) == 3300.0
        assert model_with_line_item.value("revenue", 2025) == 3600.0

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values == {2023: 3000.0, 2024: 3300.0, 2025: 3600.0}


class TestReplaceWithEmptyDict:
    """Test replacing existing line items with empty dictionary."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_with_empty_dict_clears_formula_and_values(
        self, model_with_line_item
    ):
        """Test replacing with empty dict clears both formula and values."""
        # Verify initial state
        assert model_with_line_item.value("revenue", 2023) == 1000

        # Replace with empty dict
        model_with_line_item["revenue"] = {}

        # Verify replacement - values should be None
        assert model_with_line_item.value("revenue", 2023) is None

        # Verify attributes preserved
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "income"  # Preserved
        assert updated_item.label == "Total Revenue"  # Preserved
        assert updated_item.value_format == "currency"  # Preserved
        assert updated_item.formula is None  # Cleared
        assert updated_item.values is None  # Cleared


class TestReplaceWithLineItemOrDict:
    """Test that LineItem and dict with LineItem parameters still work."""

    @pytest.fixture
    def model_with_line_item(self):
        """Create a model with an existing line item."""
        model = Model(years=[2023, 2024, 2025])
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
            value_format="currency",
        )
        return model

    def test_replace_with_line_item_replaces_all_attributes(self, model_with_line_item):
        """Test that replacing with a LineItem object replaces all attributes."""
        # Replace with a new LineItem
        new_item = LineItem(
            name="revenue",
            category="sales",
            label="Sales Revenue",
            formula="2000",
            value_format="no_decimals",
        )
        model_with_line_item["revenue"] = new_item

        # Verify all attributes are replaced
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "sales"  # Changed
        assert updated_item.label == "Sales Revenue"  # Changed
        assert updated_item.value_format == "no_decimals"  # Changed
        assert updated_item.formula == "2000"  # Changed
        assert model_with_line_item.value("revenue", 2023) == 2000

    def test_replace_with_dict_params_replaces_all_attributes(
        self, model_with_line_item
    ):
        """Test that dict with LineItem params replaces all attributes."""
        # Replace with dict of LineItem parameters
        model_with_line_item["revenue"] = {
            "category": "sales",
            "label": "Sales Revenue",
            "formula": "3000",
            "value_format": "two_decimals",
        }

        # Verify all attributes are replaced
        updated_item = model_with_line_item._line_item_definition("revenue")
        assert updated_item.category == "sales"  # Changed
        assert updated_item.label == "Sales Revenue"  # Changed
        assert updated_item.value_format == "two_decimals"  # Changed
        assert updated_item.formula == "3000"  # Changed
        assert model_with_line_item.value("revenue", 2023) == 3000


class TestMultipleReplacements:
    """Test multiple replacements in sequence."""

    def test_replace_multiple_times(self):
        """Test that line items can be replaced multiple times."""
        model = Model(years=[2023, 2024])

        # Initial creation with formula
        model["revenue"] = LineItem(
            name="revenue",
            category="income",
            label="Total Revenue",
            formula="1000",
        )
        assert model.value("revenue", 2023) == 1000

        # First replacement: change to constant
        model["revenue"] = 2000
        assert model.value("revenue", 2023) == 2000.0
        item = model._line_item_definition("revenue")
        assert item.formula is None
        assert item.category == "income"

        # Second replacement: change to formula
        model["base"] = 500
        model["revenue"] = "base * 4"
        assert model.value("revenue", 2023) == 2000.0
        item = model._line_item_definition("revenue")
        assert item.formula == "base * 4"
        assert item.values is None
        assert item.category == "income"

        # Third replacement: change to list
        model["revenue"] = [3000, 3300]
        assert model.value("revenue", 2023) == 3000.0
        assert model.value("revenue", 2024) == 3300.0
        item = model._line_item_definition("revenue")
        assert item.formula is None
        assert item.values == {2023: 3000.0, 2024: 3300.0}
        assert item.category == "income"
