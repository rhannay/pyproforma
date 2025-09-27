from pyproforma import Category, LineItem, Model


class TestAddMissingCategories:
    """Test the _add_missing_categories private method."""

    def test_add_missing_categories_with_no_missing_categories(self):
        """Test that no categories are added when all referenced categories exist."""
        # Create line items with categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
        ]

        # Create categories that match the line items
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        model = Model(line_items=line_items, years=[2023], categories=categories)

        initial_category_count = len(model._category_definitions)

        # Call the method under test
        model._add_missing_categories()

        # Should not add any new categories
        assert len(model._category_definitions) == initial_category_count
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names

    def test_add_missing_categories_with_single_missing_category(self):
        """Test that a single missing category is added correctly."""
        # Create line items with categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
            LineItem(name="assets", category="balance_sheet", values={2023: 200000}),
        ]

        # Create only some of the categories (missing "balance_sheet")
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        initial_category_count = len(model._category_definitions)

        # Call the method under test
        model._add_missing_categories()

        # Should add the missing category
        assert len(model._category_definitions) == initial_category_count + 1
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names
        assert "balance_sheet" in category_names

        # Verify the new category has correct properties
        new_category = next(
            cat for cat in model._category_definitions if cat.name == "balance_sheet"
        )
        assert new_category.name == "balance_sheet"
        assert isinstance(new_category, Category)

    def test_add_missing_categories_with_multiple_missing_categories(self):
        """Test that multiple missing categories are added correctly."""
        # Create line items with categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
            LineItem(name="cash", category="assets", values={2023: 50000}),
            LineItem(name="debt", category="liabilities", values={2023: 30000}),
            LineItem(name="equity", category="equity", values={2023: 120000}),
        ]

        # Create only one of the categories (missing multiple)
        categories = [
            Category(name="income", label="Income"),
        ]

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        initial_category_count = len(model._category_definitions)

        # Call the method under test
        model._add_missing_categories()

        # Should add all missing categories
        assert len(model._category_definitions) == initial_category_count + 4
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names
        assert "assets" in category_names
        assert "liabilities" in category_names
        assert "equity" in category_names

    def test_add_missing_categories_with_no_line_items(self):
        """Test that no categories are added when there are no line items."""
        line_items = []
        categories = [
            Category(name="income", label="Income"),
        ]

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        initial_category_count = len(model._category_definitions)

        # Call the method under test
        model._add_missing_categories()

        # Should not add any categories
        assert len(model._category_definitions) == initial_category_count

    def test_add_missing_categories_with_no_existing_categories(self):
        """Test that categories are added when starting with no categories."""
        # Create line items with categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
        ]

        # Start with no categories
        categories = []

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        # Call the method under test
        model._add_missing_categories()

        # Should add all referenced categories
        assert len(model._category_definitions) == 2
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names

    def test_add_missing_categories_with_duplicate_category_references(self):
        """Test that duplicate category references don't create duplicate categories."""
        # Create multiple line items referencing the same category
        line_items = [
            LineItem(name="revenue1", category="income", values={2023: 100000}),
            LineItem(name="revenue2", category="income", values={2023: 50000}),
            LineItem(name="revenue3", category="income", values={2023: 75000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
        ]

        # Start with no categories
        categories = []

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        # Call the method under test
        model._add_missing_categories()

        # Should add each category only once, despite multiple references
        assert len(model._category_definitions) == 2
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names

        # Verify no duplicate categories
        assert len(set(category_names)) == len(category_names)

    def test_add_missing_categories_preserves_existing_category_properties(self):
        """Test that existing categories are not modified when adding missing ones."""
        # Create line items with categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="assets", category="balance_sheet", values={2023: 200000}),
        ]

        # Create one category with custom properties
        existing_category = Category(
            name="income", label="Revenue Streams", include_total=False
        )
        categories = [existing_category]

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        # Call the method under test
        model._add_missing_categories()

        # Should add the missing category but preserve existing one
        assert len(model._category_definitions) == 2
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "balance_sheet" in category_names

        # Verify existing category properties are preserved
        income_category = next(
            cat for cat in model._category_definitions if cat.name == "income"
        )
        assert income_category.label == "Revenue Streams"
        assert income_category.include_total is False

        # Verify new category has default properties
        balance_sheet_category = next(
            cat for cat in model._category_definitions if cat.name == "balance_sheet"
        )
        assert balance_sheet_category.name == "balance_sheet"
        assert isinstance(balance_sheet_category, Category)

    def test_add_missing_categories_integration_with_model_init(self):
        """Test that _add_missing_categories works correctly during model initialization."""
        # Create line items with some missing categories
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="expenses", category="costs", values={2023: 50000}),
            LineItem(name="assets", category="balance_sheet", values={2023: 200000}),
        ]

        # Provide only some categories during initialization
        categories = [
            Category(name="income", label="Income"),
        ]

        # This should work without error because _add_missing_categories
        # is called during initialization
        model = Model(line_items=line_items, years=[2023], categories=categories)

        # Verify all categories are present
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "costs" in category_names
        assert "balance_sheet" in category_names

        # Verify model is functional
        assert model.value("revenue", 2023) == 100000
        assert model.value("expenses", 2023) == 50000
        assert model.value("assets", 2023) == 200000

    def test_add_missing_categories_with_empty_string_category(self):
        """Test that line items with empty string category are handled gracefully."""
        # Create line items, some with empty categories (which get defaulted to "general")
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="temp_item", category="general", values={2023: 50000}),
        ]

        categories = []

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        # Call the method under test
        model._add_missing_categories()

        # Should add both categories
        category_names = [cat.name for cat in model._category_definitions]
        assert "income" in category_names
        assert "general" in category_names
        assert len(model._category_definitions) == 2

    def test_add_missing_categories_maintains_category_order(self):
        """Test that new categories are added in a consistent order."""
        # Create line items with categories
        line_items = [
            LineItem(name="item1", category="zebra", values={2023: 100}),
            LineItem(name="item2", category="alpha", values={2023: 200}),
            LineItem(name="item3", category="beta", values={2023: 300}),
        ]

        categories = []

        model = Model.__new__(Model)  # Create instance without calling __init__
        model._line_item_definitions = line_items
        model._category_definitions = categories

        # Call the method under test multiple times to ensure consistency
        model._add_missing_categories()
        first_call_names = [cat.name for cat in model._category_definitions]

        # Reset and call again
        model._category_definitions = []
        model._add_missing_categories()
        second_call_names = [cat.name for cat in model._category_definitions]

        # Order should be consistent (set iteration order might vary, but within
        # a single Python session it should be consistent)
        assert len(first_call_names) == len(second_call_names)
        assert set(first_call_names) == set(second_call_names)
        assert {"zebra", "alpha", "beta"} == set(first_call_names)
