import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.results import LineItemResults, LineItemsResults


# Module-level fixtures available to all test classes
@pytest.fixture
def basic_line_items():
    """Create basic line items for testing."""
    return [
        LineItem(
            name="product_sales",
            category="income",
            label="Product Sales",
            values={2023: 100000, 2024: 120000, 2025: 140000},
            value_format="no_decimals",
        ),
        LineItem(
            name="service_revenue",
            category="income",
            label="Service Revenue",
            values={2023: 50000, 2024: 60000, 2025: 70000},
            value_format="no_decimals",
        ),
        LineItem(
            name="salaries",
            category="costs",
            label="Salaries",
            values={2023: 40000, 2024: 45000, 2025: 50000},
            value_format="no_decimals",
        ),
        LineItem(
            name="office_rent",
            category="costs",
            label="Office Rent",
            values={2023: 24000, 2024: 24000, 2025: 24000},
            value_format="no_decimals",
        ),
    ]


@pytest.fixture
def basic_categories():
    """Create basic categories for testing."""
    return [
        Category(name="income", label="Income"),
        Category(name="costs", label="Costs"),
        Category(name="metrics", label="Metrics"),
    ]


@pytest.fixture
def model_with_line_items(basic_line_items, basic_categories):
    """Create a model with line items for testing."""
    return Model(
        line_items=basic_line_items,
        years=[2023, 2024, 2025],
        categories=basic_categories,
    )


class TestLineItemsResultsInitialization:
    """Test LineItemsResults initialization and basic properties."""

    def test_init_valid_line_items(self, model_with_line_items):
        """Test LineItemsResults initialization with valid line items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        assert items.model is model_with_line_items
        assert len(items.names) == 2
        assert "product_sales" in items.names
        assert "service_revenue" in items.names

    def test_init_single_line_item(self, model_with_line_items):
        """Test LineItemsResults initialization with a single line item."""
        items = LineItemsResults(model_with_line_items, ["product_sales"])

        assert items.model is model_with_line_items
        assert len(items.names) == 1
        assert items.names == ["product_sales"]

    def test_init_all_line_items(self, model_with_line_items):
        """Test LineItemsResults initialization with all line items."""
        all_names = model_with_line_items.line_item_names
        items = LineItemsResults(model_with_line_items, all_names)

        assert items.model is model_with_line_items
        assert len(items.names) == 4
        assert set(items.names) == set(all_names)

    def test_init_empty_list_raises_error(self, model_with_line_items):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(model_with_line_items, [])
        assert "non-empty list" in str(exc_info.value)

    def test_init_none_raises_error(self, model_with_line_items):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(model_with_line_items, None)
        assert "must be a list" in str(exc_info.value)

    def test_init_string_raises_error(self, model_with_line_items):
        """Test that passing a string instead of list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(model_with_line_items, "product_sales")
        assert "must be a list" in str(exc_info.value)

    def test_init_tuple_raises_error(self, model_with_line_items):
        """Test that passing a tuple instead of list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(
                model_with_line_items, ("product_sales", "service_revenue")
            )
        assert "must be a list" in str(exc_info.value)

    def test_init_set_raises_error(self, model_with_line_items):
        """Test that passing a set instead of list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(
                model_with_line_items, {"product_sales", "service_revenue"}
            )
        assert "must be a list" in str(exc_info.value)

    def test_init_integer_raises_error(self, model_with_line_items):
        """Test that passing an integer instead of list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(model_with_line_items, 123)
        assert "must be a list" in str(exc_info.value)

    def test_init_dict_raises_error(self, model_with_line_items):
        """Test that passing a dict instead of list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LineItemsResults(
                model_with_line_items, {"product_sales": 1, "service_revenue": 2}
            )
        assert "must be a list" in str(exc_info.value)

    def test_init_invalid_line_item_name_raises_error(self, model_with_line_items):
        """Test that invalid line item name raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            LineItemsResults(model_with_line_items, ["nonexistent"])
        assert "nonexistent" in str(exc_info.value)
        assert "not found in model" in str(exc_info.value)

    def test_init_mixed_valid_invalid_names_raises_error(self, model_with_line_items):
        """Test that having one invalid name in the list raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            LineItemsResults(
                model_with_line_items, ["product_sales", "invalid_name", "salaries"]
            )
        assert "invalid_name" in str(exc_info.value)


class TestLineItemsResultsNamesProperty:
    """Test the names property of LineItemsResults."""

    def test_names_property_returns_list(self, model_with_line_items):
        """Test that names property returns a list of line item names."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        names = items.names
        assert isinstance(names, list)
        assert len(names) == 2
        assert names == ["product_sales", "service_revenue"]

    def test_names_property_returns_copy(self, model_with_line_items):
        """Test that names property returns a copy, not the original list."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        names = items.names
        names.append("salaries")

        # Original should not be modified
        assert len(items.names) == 2
        assert "salaries" not in items.names

    def test_names_property_preserves_order(self, model_with_line_items):
        """Test that names property preserves the order of line items."""
        items = LineItemsResults(
            model_with_line_items, ["salaries", "product_sales", "office_rent"]
        )

        names = items.names
        assert names == ["salaries", "product_sales", "office_rent"]


class TestLineItemsResultsSetCategoryMethod:
    """Test the set_category method of LineItemsResults."""

    def test_set_category_updates_all_items(self, model_with_line_items):
        """Test that set_category updates category for all line items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        # Set category to 'costs'
        items.set_category("costs")

        # Verify both items now have 'costs' category
        product_sales = model_with_line_items.line_item("product_sales")
        service_revenue = model_with_line_items.line_item("service_revenue")

        assert product_sales.category == "costs"
        assert service_revenue.category == "costs"

    def test_set_category_creates_new_category(self, model_with_line_items):
        """Test that set_category creates a new category if it doesn't exist."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        # Set to a new category
        items.set_category("new_category")

        # Verify category was created and items were updated
        assert "new_category" in model_with_line_items.category_names
        product_sales = model_with_line_items.line_item("product_sales")
        assert product_sales.category == "new_category"

    def test_set_category_with_single_item(self, model_with_line_items):
        """Test set_category with a single line item."""
        items = LineItemsResults(model_with_line_items, ["product_sales"])

        items.set_category("metrics")

        product_sales = model_with_line_items.line_item("product_sales")
        assert product_sales.category == "metrics"

    def test_set_category_with_multiple_items_different_categories(
        self, model_with_line_items
    ):
        """Test set_category with items from different original categories."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "salaries", "office_rent"]
        )

        # Original categories: product_sales=income, salaries=costs, office_rent=costs
        items.set_category("expenses")

        # Verify all items now have 'expenses' category
        for name in ["product_sales", "salaries", "office_rent"]:
            item = model_with_line_items.line_item(name)
            assert item.category == "expenses"


class TestLineItemsResultsLineItemMethod:
    """Test the line_item method of LineItemsResults."""

    def test_line_item_returns_line_item_results(self, model_with_line_items):
        """Test that line_item returns a LineItemResults object."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        result = items.line_item("product_sales")

        assert isinstance(result, LineItemResults)
        assert result.name == "product_sales"
        assert result.model is model_with_line_items

    def test_line_item_returns_correct_item(self, model_with_line_items):
        """Test that line_item returns the correct LineItemResults."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue", "salaries"]
        )

        # Get each item and verify
        product_sales = items.line_item("product_sales")
        service_revenue = items.line_item("service_revenue")
        salaries = items.line_item("salaries")

        assert product_sales.name == "product_sales"
        assert service_revenue.name == "service_revenue"
        assert salaries.name == "salaries"

    def test_line_item_raises_error_for_non_included_item(self, model_with_line_items):
        """Test that line_item raises KeyError for non-included items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        # salaries exists in model but not in this LineItemsResults
        with pytest.raises(KeyError) as exc_info:
            items.line_item("salaries")

        assert "salaries" in str(exc_info.value)
        assert "not found in this LineItemsResults" in str(exc_info.value)

    def test_line_item_raises_error_for_invalid_item(self, model_with_line_items):
        """Test that line_item raises KeyError for completely invalid items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        with pytest.raises(KeyError) as exc_info:
            items.line_item("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_line_item_can_access_all_included_items(self, model_with_line_items):
        """Test that all included items can be accessed via line_item."""
        all_names = ["product_sales", "service_revenue", "salaries", "office_rent"]
        items = LineItemsResults(model_with_line_items, all_names)

        # Should be able to access all items without error
        for name in all_names:
            result = items.line_item(name)
            assert result.name == name


class TestLineItemsResultsDisplayMethods:
    """Test display and summary methods of LineItemsResults."""

    def test_str_returns_summary(self, model_with_line_items):
        """Test that __str__ returns the summary."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        str_repr = str(items)

        assert "LineItemsResults" in str_repr
        assert "Number of Items: 2" in str_repr
        assert "product_sales" in str_repr
        assert "service_revenue" in str_repr

    def test_repr_shows_num_items(self, model_with_line_items):
        """Test that __repr__ shows number of items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue", "salaries"]
        )

        repr_str = repr(items)

        assert "LineItemsResults" in repr_str
        assert "num_items=3" in repr_str

    def test_summary_plain_text(self, model_with_line_items):
        """Test summary method with plain text output."""
        items = LineItemsResults(model_with_line_items, ["product_sales", "salaries"])

        summary = items.summary(html=False)

        assert "LineItemsResults" in summary
        assert "Number of Items: 2" in summary
        assert "product_sales, salaries" in summary
        assert "<br>" not in summary

    def test_summary_html(self, model_with_line_items):
        """Test summary method with HTML output."""
        items = LineItemsResults(model_with_line_items, ["product_sales", "salaries"])

        summary = items.summary(html=True)

        assert "<pre>" in summary
        assert "</pre>" in summary
        assert "<br>" in summary
        assert "LineItemsResults" in summary

    def test_repr_html(self, model_with_line_items):
        """Test _repr_html_ method for Jupyter notebooks."""
        items = LineItemsResults(model_with_line_items, ["product_sales", "salaries"])

        html = items._repr_html_()

        assert "<pre>" in html
        assert "</pre>" in html
        assert "<br>" in html


class TestLineItemsResultsModelIntegration:
    """Test integration with Model.line_items() method."""

    def test_model_line_items_method_returns_line_items_results(
        self, model_with_line_items
    ):
        """Test that Model.line_items() returns LineItemsResults."""
        items = model_with_line_items.line_items(["product_sales", "service_revenue"])

        assert isinstance(items, LineItemsResults)
        assert items.model is model_with_line_items
        assert len(items.names) == 2

    def test_model_line_items_with_empty_list_raises_error(self, model_with_line_items):
        """Test that Model.line_items() with empty list raises error."""
        with pytest.raises(ValueError):
            model_with_line_items.line_items([])

    def test_model_line_items_with_invalid_name_raises_error(
        self, model_with_line_items
    ):
        """Test that Model.line_items() with invalid name raises error."""
        with pytest.raises(KeyError):
            model_with_line_items.line_items(["invalid_name"])

    def test_model_line_items_end_to_end(self, model_with_line_items):
        """Test end-to-end usage of Model.line_items()."""
        # Get multiple line items
        items = model_with_line_items.line_items(
            ["product_sales", "service_revenue", "salaries"]
        )

        # Check names
        assert set(items.names) == {"product_sales", "service_revenue", "salaries"}

        # Set category for all
        items.set_category("financial_items")

        # Verify category was set
        for name in items.names:
            item = model_with_line_items.line_item(name)
            assert item.category == "financial_items"

        # Get individual item
        product_sales = items.line_item("product_sales")
        assert product_sales.name == "product_sales"
        assert product_sales.category == "financial_items"


class TestLineItemsResultsEdgeCases:
    """Test edge cases and error handling."""

    def test_duplicate_names_in_list(self, model_with_line_items):
        """Test that duplicate names in the list are handled."""
        # Should not raise an error, but might want to deduplicate
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "product_sales"]
        )

        # Both instances refer to the same item
        assert len(items.names) == 2
        assert items.names == ["product_sales", "product_sales"]

    def test_set_category_on_empty_model(self):
        """Test set_category with model that has no categories."""
        model = Model(years=[2023, 2024])
        model.update.add_line_item(
            name="item1", category="cat1", values={2023: 100, 2024: 200}
        )
        model.update.add_line_item(
            name="item2", category="cat1", values={2023: 150, 2024: 250}
        )

        items = model.line_items(["item1", "item2"])
        items.set_category("new_cat")

        # Should create new category
        assert "new_cat" in model.category_names
        assert model.line_item("item1").category == "new_cat"
        assert model.line_item("item2").category == "new_cat"

    def test_names_property_immutability(self, model_with_line_items):
        """Test that modifying returned names list doesn't affect internal state."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        names1 = items.names
        names1.clear()

        # Getting names again should still return the original list
        names2 = items.names
        assert len(names2) == 2
        assert "product_sales" in names2


class TestLineItemsResultsTableMethod:
    """Test the table method of LineItemsResults."""

    def test_table_returns_table_object(self, model_with_line_items):
        """Test that table method returns a Table object."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        table = items.table()

        # Should return a Table object
        assert table is not None
        assert hasattr(table, "rows")

    def test_table_includes_only_specified_line_items(self, model_with_line_items):
        """Test that table only includes the line items in this results set."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        table = items.table()

        # Check that only the specified items are in the table
        # Get all row labels (excluding potential category headers)
        row_labels = []
        for row in table.rows:
            if hasattr(row, "cells") and len(row.cells) > 0:
                cell_value = row.cells[0].value
                # Skip category headers and focus on line item labels
                if cell_value not in ["Income", "Costs"]:  # Category names
                    row_labels.append(cell_value)

        # Should contain the labels for our line items
        assert "Product Sales" in row_labels
        assert "Service Revenue" in row_labels
        # Should not contain labels for items not in the results set
        assert "Salaries" not in row_labels
        assert "Office Rent" not in row_labels

    def test_table_with_single_line_item(self, model_with_line_items):
        """Test table method with a single line item."""
        items = LineItemsResults(model_with_line_items, ["product_sales"])

        table = items.table()

        assert table is not None
        # Should have at least one row for the line item
        assert len(table.rows) >= 1

        # Check that the correct item is included
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]
        assert "Product Sales" in row_labels

    def test_table_with_group_by_category_true(self, model_with_line_items):
        """Test table method with group_by_category=True."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue", "salaries"]
        )

        table = items.table(group_by_category=True)

        assert table is not None

        # Should include category headers
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        # Should have category headers
        assert "Income" in row_labels  # Category for product_sales and service_revenue
        assert "Costs" in row_labels  # Category for salaries
        # And the line item labels
        assert "Product Sales" in row_labels
        assert "Service Revenue" in row_labels
        assert "Salaries" in row_labels

    def test_table_with_include_percent_change_true(self, model_with_line_items):
        """Test table method with include_percent_change=True."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        table = items.table(include_percent_change=True)

        assert table is not None

        # Should have more rows due to percent change rows
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        # Should include both item labels and percent change labels
        assert "Product Sales" in row_labels
        assert "Product Sales % Change" in row_labels
        assert "Service Revenue" in row_labels
        assert "Service Revenue % Change" in row_labels

    def test_table_with_included_cols(self, model_with_line_items):
        """Test table method with custom included_cols."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        table = items.table(included_cols=["name", "label"])

        assert table is not None
        # Table should be created successfully with custom columns
        assert len(table.rows) >= 2  # At least one row per line item

    def test_table_with_hardcoded_color(self, model_with_line_items):
        """Test table method with hardcoded_color parameter."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        table = items.table(hardcoded_color="blue")

        assert table is not None
        # Should create table successfully with color parameter
        assert len(table.rows) >= 2

    def test_table_with_multiple_kwargs(self, model_with_line_items):
        """Test table method with multiple keyword arguments."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue", "salaries"]
        )

        table = items.table(
            group_by_category=True,
            include_percent_change=True,
            included_cols=["label"],
            hardcoded_color="red",
        )

        assert table is not None
        # Should handle multiple parameters without error
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        # Should have category grouping and percent changes
        assert "Income" in row_labels
        assert "Product Sales" in row_labels
        assert "Product Sales % Change" in row_labels

    def test_table_with_all_line_items(self, model_with_line_items):
        """Test table method when results set includes all line items."""
        all_names = model_with_line_items.line_item_names
        items = LineItemsResults(model_with_line_items, all_names)

        table = items.table()

        assert table is not None

        # Should include all line item labels
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]

        assert "Product Sales" in row_labels
        assert "Service Revenue" in row_labels
        assert "Salaries" in row_labels
        assert "Office Rent" in row_labels

    def test_table_filters_correctly_from_model_items(self, model_with_line_items):
        """Test that table correctly filters from the full model."""
        # Create results with subset of items
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "office_rent"]
        )

        table = items.table()

        # Get the line item labels from the table
        row_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells")
            and len(row.cells) > 0
            and row.cells[0].value not in ["Income", "Costs"]  # Skip category headers
        ]

        # Should only contain the specified items
        assert "Product Sales" in row_labels
        assert "Office Rent" in row_labels
        # Should not contain the items not in the results set
        assert "Service Revenue" not in row_labels
        assert "Salaries" not in row_labels

    def test_table_uses_model_tables_line_items(self, model_with_line_items):
        """Test that table method properly delegates to model.tables.line_items."""
        items = LineItemsResults(
            model_with_line_items, ["product_sales", "service_revenue"]
        )

        # Call table method
        table = items.table(group_by_category=True)

        # Verify it produces the same result as calling model.tables.line_items directly
        direct_table = model_with_line_items.tables.line_items(
            line_item_names=["product_sales", "service_revenue"], group_by_category=True
        )

        # Should have the same number of rows
        assert len(table.rows) == len(direct_table.rows)

        # Should have the same row labels
        table_labels = [
            row.cells[0].value
            for row in table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]
        direct_labels = [
            row.cells[0].value
            for row in direct_table.rows
            if hasattr(row, "cells") and len(row.cells) > 0
        ]
        assert table_labels == direct_labels
