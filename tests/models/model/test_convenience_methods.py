"""
Tests for Model convenience methods: add_line_item and add_category.

These methods provide a direct interface to the update namespace functionality.
"""

import pytest

from pyproforma import Category, LineItem, Model


class TestAddLineItemConvenienceMethod:
    """Test the Model.add_line_item convenience method."""

    def test_add_line_item_with_parameters(self):
        """Test adding a line item using parameters."""
        model = Model(years=[2023, 2024])

        # Add a category first
        model.add_category(name="revenue")

        # Add line item with parameters
        model.add_line_item(
            name="sales",
            category="revenue",
            values={2023: 100000, 2024: 110000},
            label="Sales Revenue",
        )

        assert "sales" in model.line_item_names
        assert model.value("sales", 2023) == 100000
        assert model.value("sales", 2024) == 110000

    def test_add_line_item_with_instance(self):
        """Test adding a line item using a LineItem instance."""
        model = Model(years=[2023, 2024])

        # Add a category first
        model.add_category(name="revenue")

        # Create LineItem instance
        line_item = LineItem(
            name="sales", category="revenue", values={2023: 100000, 2024: 110000}
        )

        # Add line item with instance
        model.add_line_item(line_item)

        assert "sales" in model.line_item_names
        assert model.value("sales", 2023) == 100000

    def test_add_line_item_with_formula(self):
        """Test adding a line item with a formula."""
        model = Model(years=[2023, 2024])

        # Add categories
        model.add_category(name="revenue")
        model.add_category(name="expenses")

        # Add base line item
        model.add_line_item(
            name="sales", category="revenue", values={2023: 100000, 2024: 110000}
        )

        # Add line item with formula
        model.add_line_item(
            name="commission", category="expenses", formula="sales * 0.1"
        )

        assert model.value("commission", 2023) == 10000.0
        assert model.value("commission", 2024) == 11000.0

    def test_add_line_item_no_parameters_raises_error(self):
        """Test that calling add_line_item without parameters raises an error."""
        model = Model(years=[2023, 2024])

        with pytest.raises(
            ValueError,
            match="Must specify either 'line_item' parameter or 'name' parameter",
        ):
            model.add_line_item()

    def test_add_line_item_both_instance_and_name_raises_error(self):
        """Test that providing both line_item and name raises an error."""
        model = Model(years=[2023, 2024])
        line_item = LineItem(name="test")

        with pytest.raises(
            ValueError, match="Cannot specify both 'line_item' and 'name' parameters"
        ):
            model.add_line_item(line_item=line_item, name="test")

    def test_add_line_item_duplicate_name_raises_error(self):
        """Test that adding a line item with an existing name raises an error."""
        model = Model(years=[2023, 2024])

        # Add a category first
        model.add_category(name="revenue")

        # Add first line item
        model.add_line_item(name="sales", category="revenue", values={2023: 100000})

        # Try to add another line item with the same name
        with pytest.raises(
            ValueError,
            match="Line item with name 'sales' already exists. Use update.update_line_item\\(\\) to modify existing line items.",
        ):
            model.add_line_item(name="sales", category="revenue", values={2023: 150000})

    def test_add_line_item_duplicate_name_with_instance_raises_error(self):
        """Test that adding a LineItem instance with an existing name raises an error."""
        model = Model(years=[2023, 2024])

        # Add a category first
        model.add_category(name="revenue")

        # Add first line item
        model.add_line_item(name="sales", category="revenue", values={2023: 100000})

        # Try to add another line item instance with the same name
        duplicate_line_item = LineItem(
            name="sales", category="revenue", values={2023: 150000}
        )
        with pytest.raises(
            ValueError,
            match="Line item with name 'sales' already exists. Use update.update_line_item\\(\\) to modify existing line items.",
        ):
            model.add_line_item(duplicate_line_item)

    def test_add_line_item_delegates_to_update_namespace(self):
        """Test that add_line_item produces the same result as update.add_line_item."""
        # Create two identical models
        model1 = Model(years=[2023, 2024])
        model2 = Model(years=[2023, 2024])

        # Add categories to both
        model1.add_category(name="revenue")
        model2.update.add_category(name="revenue")

        # Add line item using convenience method vs update namespace
        model1.add_line_item(name="sales", category="revenue", values={2023: 100000})
        model2.update.add_line_item(
            name="sales", category="revenue", values={2023: 100000}
        )

        # Should produce identical results
        assert model1.line_item_names == model2.line_item_names
        assert model1.value("sales", 2023) == model2.value("sales", 2023)


class TestAddCategoryConvenienceMethod:
    """Test the Model.add_category convenience method."""

    def test_add_category_with_parameters(self):
        """Test adding a category using parameters."""
        model = Model(years=[2023, 2024])

        model.add_category(
            name="assets", label="Assets & Inventory", include_total=True
        )

        assert "assets" in model.category_names

    def test_add_category_with_instance(self):
        """Test adding a category using a Category instance."""
        model = Model(years=[2023, 2024])

        # Create Category instance
        category = Category(name="assets", label="Assets & Inventory")

        # Add category with instance
        model.add_category(category)

        assert "assets" in model.category_names

    def test_add_category_no_parameters_raises_error(self):
        """Test that calling add_category without parameters raises an error."""
        model = Model(years=[2023, 2024])

        with pytest.raises(
            ValueError,
            match="Must specify either 'category' parameter or 'name' parameter",
        ):
            model.add_category()

    def test_add_category_both_instance_and_name_raises_error(self):
        """Test that providing both category and name raises an error."""
        model = Model(years=[2023, 2024])
        category = Category(name="test")

        with pytest.raises(
            ValueError, match="Cannot specify both 'category' and 'name' parameters"
        ):
            model.add_category(category=category, name="test")

    def test_add_category_delegates_to_update_namespace(self):
        """Test that add_category produces the same result as update.add_category."""
        # Create two identical models
        model1 = Model(years=[2023, 2024])
        model2 = Model(years=[2023, 2024])

        # Add category using convenience method vs update namespace
        model1.add_category(name="assets", label="Assets")
        model2.update.add_category(name="assets", label="Assets")

        # Should produce identical results
        assert model1.category_names == model2.category_names


class TestConvenienceMethodsIntegration:
    """Test that both convenience methods work together."""

    def test_full_workflow_with_convenience_methods(self):
        """Test a complete workflow using only convenience methods."""
        model = Model(years=[2023, 2024, 2025])

        # Add categories
        model.add_category(name="revenue", label="Revenue Streams")
        model.add_category(name="expenses", label="Operating Expenses")
        model.add_category(name="profit", label="Profitability")

        # Add revenue line items
        model.add_line_item(
            name="product_sales",
            category="revenue",
            values={2023: 800000, 2024: 900000, 2025: 1000000},
        )

        model.add_line_item(
            name="service_revenue",
            category="revenue",
            values={2023: 200000, 2024: 250000, 2025: 300000},
        )

        # Add expense line items
        model.add_line_item(
            name="salaries",
            category="expenses",
            values={2023: 400000, 2024: 450000, 2025: 500000},
        )

        model.add_line_item(
            name="marketing", category="expenses", formula="total_revenue * 0.1"
        )

        # Add profit calculation
        model.add_line_item(
            name="net_profit",
            category="profit",
            formula="total_revenue - total_expenses",
        )

        # Verify all items were added correctly
        expected_line_items = [
            "product_sales",
            "service_revenue",
            "salaries",
            "marketing",
            "net_profit",
            "total_revenue",
            "total_expenses",
            "total_profit",
        ]
        for item in expected_line_items:
            assert item in model.line_item_names

        # Verify calculations
        assert model.value("total_revenue", 2023) == 1000000
        assert model.value("marketing", 2023) == 100000  # 10% of revenue
        assert model.value("net_profit", 2023) == 500000  # Revenue - expenses
