import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.generator.debt import Debt
from pyproforma.models.metadata import (
    generate_category_metadata,
    generate_line_item_metadata,
)
from pyproforma.models.model.value_matrix import (
    _calculate_category_total,
    generate_value_matrix,
)


class TestGenerateValueMatrix:
    """Test cases for the generate_value_matrix() function."""

    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="revenue", label="Revenue"),
            Category(name="expenses", label="Expenses"),
            Category(name="net_income", label="Net Income"),
        ]

    def test_order_of_line_items_does_not_matter(self, basic_categories):
        """Test that the order of line items in the list does not affect the calculation results."""  # noqa: E501
        # Create line items with dependencies - net_income depends on revenue and expenses  # noqa: E501
        revenue = LineItem(
            name="revenue", category="revenue", values={2023: 1000, 2024: 1200}
        )
        expenses = LineItem(
            name="expenses", category="expenses", values={2023: 600, 2024: 700}
        )
        net_income = LineItem(
            name="net_income", category="net_income", formula="revenue - expenses"
        )

        # Create models with different orders of the same line items
        model1 = Model(
            line_items=[revenue, expenses, net_income],  # Dependencies first
            years=[2023, 2024],
            categories=basic_categories,
        )

        model2 = Model(
            line_items=[net_income, revenue, expenses],  # Dependent item first
            years=[2023, 2024],
            categories=basic_categories,
        )

        model3 = Model(
            line_items=[expenses, net_income, revenue],  # Mixed order
            years=[2023, 2024],
            categories=basic_categories,
        )

        # All models should produce the same value matrix
        matrix1 = generate_value_matrix(
            model1.years,
            model1._line_item_definitions + model1.generators,
            model1.category_metadata,
            model1.line_item_metadata,
        )
        matrix2 = generate_value_matrix(
            model2.years,
            model2._line_item_definitions + model2.generators,
            model2.category_metadata,
            model2.line_item_metadata,
        )
        matrix3 = generate_value_matrix(
            model3.years,
            model3._line_item_definitions + model3.generators,
            model3.category_metadata,
            model3.line_item_metadata,
        )

        # Verify all matrices are identical
        for year in [2023, 2024]:
            assert matrix1[year] == matrix2[year] == matrix3[year]
            # Verify specific calculations are correct
            assert matrix1[year]["revenue"] == revenue.values[year]
            assert matrix1[year]["expenses"] == expenses.values[year]
            assert (
                matrix1[year]["net_income"]
                == revenue.values[year] - expenses.values[year]
            )

    def test_order_with_complex_dependencies(self, basic_categories):
        """Test order independence with more complex dependency chains."""
        # Create a chain: base -> intermediate -> final
        base = LineItem(name="base", category="revenue", values={2023: 100})
        intermediate = LineItem(
            name="intermediate", category="revenue", formula="base * 2"
        )
        final = LineItem(
            name="final", category="revenue", formula="intermediate + base"
        )

        # Try different orders
        model1 = Model(
            line_items=[base, intermediate, final],
            years=[2023],
            categories=basic_categories,
        )

        model2 = Model(
            line_items=[final, intermediate, base],
            years=[2023],
            categories=basic_categories,
        )

        matrix1 = generate_value_matrix(
            model1.years,
            model1._line_item_definitions + model1.generators,
            model1.category_metadata,
            model1.line_item_metadata,
        )
        matrix2 = generate_value_matrix(
            model2.years,
            model2._line_item_definitions + model2.generators,
            model2.category_metadata,
            model2.line_item_metadata,
        )

        assert matrix1[2023] == matrix2[2023]
        assert matrix1[2023]["base"] == 100
        assert matrix1[2023]["intermediate"] == 200
        assert matrix1[2023]["final"] == 300

    def test_formula_with_invalid_variable_raises_useful_exception(
        self, basic_categories
    ):
        """Test that a formula with an unknown variable raises a clear exception."""
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        # Formula references 'unknown_variable' which doesn't exist
        invalid_item = LineItem(
            name="invalid_calculation",
            category="expenses",
            formula="revenue - unknown_variable",
        )

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [revenue, invalid_item]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_definitions,
                line_item_metadata,
            )

        # Verify the exception message is useful - should detect invalid variable
        error_msg = str(exc_info.value)
        assert "'unknown_variable' not found" in error_msg

    def test_circular_reference_simple(self, basic_categories):
        """Test detection of simple circular references."""
        # Create circular dependency: a depends on b, b depends on a
        item_a = LineItem(name="item_a", category="revenue", formula="item_b + 10")
        item_b = LineItem(name="item_b", category="revenue", formula="item_a - 5")

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [item_a, item_b]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_metadata,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        assert (
            "Could not calculate line items due to missing dependencies or circular references"  # noqa: E501
            in error_msg
        )
        # Both items should be mentioned as they're both unresolvable
        assert "item_a" in error_msg
        assert "item_b" in error_msg

    def test_circular_reference_complex(self, basic_categories):
        """Test detection of complex circular references involving multiple items."""
        # Create circular dependency chain: a -> b -> c -> a
        item_a = LineItem(name="item_a", category="revenue", formula="item_c + 10")
        item_b = LineItem(name="item_b", category="revenue", formula="item_a * 2")
        item_c = LineItem(name="item_c", category="revenue", formula="item_b - 5")
        # Add a non-circular item to ensure it still gets calculated
        item_d = LineItem(name="item_d", category="revenue", values={2023: 100})

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [item_a, item_b, item_c, item_d]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_metadata,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        assert (
            "Could not calculate line items due to missing dependencies or circular references"  # noqa: E501
            in error_msg
        )
        # All three circular items should be mentioned
        assert "item_a" in error_msg
        assert "item_b" in error_msg
        assert "item_c" in error_msg
        # item_d should not be mentioned since it's not part of the circular reference
        assert "item_d" not in error_msg

    def test_self_reference_circular(self, basic_categories):
        """Test detection of self-referencing formulas."""
        # Item that references itself
        self_ref = LineItem(name="self_ref", category="revenue", formula="self_ref + 1")

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [self_ref]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_metadata,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        assert (
            "Could not calculate line items due to missing dependencies or circular references"  # noqa: E501
            in error_msg
        )
        assert "self_ref" in error_msg

    def test_partial_circular_reference(self, basic_categories):
        """Test that items not involved in circular references still get calculated."""
        # Create items where some are circular but others are not
        good_item1 = LineItem(name="good1", category="revenue", values={2023: 100})
        good_item2 = LineItem(name="good2", category="revenue", formula="good1 * 2")

        # Circular items
        bad_item1 = LineItem(name="bad1", category="expenses", formula="bad2 + 10")
        bad_item2 = LineItem(name="bad2", category="expenses", formula="bad1 - 5")

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [good_item1, good_item2, bad_item1, bad_item2]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_metadata,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        # Only the circular items should be mentioned
        assert "bad1" in error_msg
        assert "bad2" in error_msg
        assert "good1" not in error_msg
        assert "good2" not in error_msg

    def test_generate_value_matrix_with_line_item_generators(self, basic_categories):
        """Test that line item generators are included in the value matrix and order doesn't matter."""  # noqa: E501
        # Create a debt line item generator
        debt_generator = Debt(
            name="loan", par_amount={2023: 100000}, interest_rate=0.05, term=5
        )

        # Create line items that depend on line item generator values
        revenue = LineItem(name="revenue", category="revenue", values={2023: 150000})
        # Use the first defined name from the line item generator
        debt_names = debt_generator.defined_names
        debt_payment_var = debt_names[0]  # Usually something like "loan_principal"

        net_income = LineItem(
            name="net_income",
            category="net_income",
            formula=f"revenue - {debt_payment_var}",
        )

        # Test different orders
        model1 = Model(
            line_items=[revenue, net_income],
            years=[2023],
            categories=basic_categories,
            generators=[debt_generator],
        )

        model2 = Model(
            line_items=[net_income, revenue],  # Different order
            years=[2023],
            categories=basic_categories,
            generators=[debt_generator],
        )

        matrix1 = generate_value_matrix(
            model1.years,
            model1._line_item_definitions + model1.generators,
            model1.category_metadata,
            model1.line_item_metadata,
        )
        matrix2 = generate_value_matrix(
            model2.years,
            model2._line_item_definitions + model2.generators,
            model2.category_metadata,
            model2.line_item_metadata,
        )

        # Both should produce the same result
        assert matrix1[2023] == matrix2[2023]

        # Verify line item generator values are included
        for debt_name in debt_names:
            assert debt_name in matrix1[2023]
            assert isinstance(matrix1[2023][debt_name], (int, float))

        # Verify line items calculated correctly
        assert matrix1[2023]["revenue"] == 150000
        assert matrix1[2023]["net_income"] == 150000 - matrix1[2023][debt_payment_var]

    def test_generate_value_matrix_with_assumptions(self, basic_categories):
        """Test that assumptions (now as line items) are included in the value matrix."""  # noqa: E501
        # Create assumptions as line items
        growth_rate = LineItem(
            name="growth_rate", category="assumptions", values={2023: 0.05, 2024: 0.07}
        )
        base_value = LineItem(
            name="base_value", category="assumptions", values={2023: 1000, 2024: 1200}
        )

        # Create line items that use assumptions
        calculated_revenue = LineItem(
            name="calculated_revenue",
            category="revenue",
            formula="base_value * (1 + growth_rate)",
        )

        # Add assumptions category
        assumption_category = Category(name="assumptions", label="Assumptions")
        all_categories = basic_categories + [assumption_category]

        model = Model(
            line_items=[calculated_revenue, growth_rate, base_value],
            years=[2023, 2024],
            categories=all_categories,
        )

        matrix = generate_value_matrix(
            model.years,
            model._line_item_definitions + model.generators,
            model.category_metadata,
            model.line_item_metadata,
        )

        # Verify assumptions are in the matrix
        for year in [2023, 2024]:
            assert "growth_rate" in matrix[year]
            assert "base_value" in matrix[year]
            assert matrix[year]["growth_rate"] == growth_rate.values[year]
            assert matrix[year]["base_value"] == base_value.values[year]

            # Verify calculation using assumptions
            expected_revenue = base_value.values[year] * (1 + growth_rate.values[year])
            assert matrix[year]["calculated_revenue"] == expected_revenue

    def test_missing_dependency_clear_error(self, basic_categories):
        """Test that missing dependencies produce clear error messages."""
        # Create item that depends on non-existent variable
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        dependent = LineItem(
            name="dependent_item",
            category="expenses",
            formula="revenue + nonexistent_variable",
        )

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [revenue, dependent]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_definitions,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        assert "'nonexistent_variable' not found" in error_msg

    def test_formula_referencing_own_category_total_raises_error(
        self, basic_categories
    ):
        """Test that a formula referencing its own category total raises a clear error."""  # noqa: E501
        # Suppose the convention is that category totals are referenced as e.g. 'revenue_total'  # noqa: E501
        revenue = LineItem(name="revenue", category="revenue", values={2023: 1000})
        # This line item tries to reference its own category total, which should not be allowed  # noqa: E501
        bad_item = LineItem(
            name="bad_item", category="revenue", formula="revenue_total + 100"
        )

        # Prepare parameters for generate_value_matrix directly
        years = [2023]
        line_item_definitions = [revenue, bad_item]
        category_definitions = basic_categories
        multi_line_items = []

        # Create metadata needed for generate_value_matrix
        category_metadata = generate_category_metadata(
            category_definitions, multi_line_items
        )
        line_item_metadata = generate_line_item_metadata(
            line_item_definitions,
            category_metadata,
            multi_line_items,
        )

        with pytest.raises(ValueError) as exc_info:
            generate_value_matrix(
                years,
                line_item_definitions + multi_line_items,
                category_definitions,
                line_item_metadata,
            )

        error_msg = str(exc_info.value)
        # The error should mention that referencing own category total is not allowed or not found  # noqa: E501
        assert "revenue_total" in error_msg
        assert "not found" in error_msg or "not allowed" in error_msg

    def test_category_total_circular_reference_error(self, basic_categories):
        """Test that using category_total formula for own category raises clear error."""  # noqa: E501
        # Create line items where one tries to use category_total for its own category
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        revenue2 = LineItem(name="revenue2", category="revenue", values={2023: 500})

        # This line item is in "revenue" category and tries to total that same category
        # This creates a circular reference
        total_revenue = LineItem(
            name="total_revenue",
            category="revenue",  # Same as the category being totaled
            formula="category_total:revenue"
        )

        line_items = [revenue1, revenue2, total_revenue]

        # This should raise a ValueError with a clear message about circular reference
        with pytest.raises(ValueError) as exc_info:
            Model(
                line_items=line_items,
                years=[2023],
                categories=basic_categories
            )

        error_msg = str(exc_info.value)
        # Check for specific error message components
        assert "Circular reference detected" in error_msg
        assert "total_revenue" in error_msg
        assert "category_total:revenue" in error_msg
        assert "revenue" in error_msg
        assert "circular dependency" in error_msg.lower()

    def test_order_with_category_total_dependencies(self, basic_categories):
        """Test that order of line items does not affect calculation when using category totals."""  # noqa: E501
        # Add two revenue and two expense line items
        rev1 = LineItem(name="rev1", category="revenue", values={2023: 100, 2024: 200})
        rev2 = LineItem(name="rev2", category="revenue", values={2023: 300, 2024: 400})
        exp1 = LineItem(name="exp1", category="expenses", values={2023: 50, 2024: 60})
        exp2 = LineItem(name="exp2", category="expenses", values={2023: 70, 2024: 80})
        # net_revenues depends on category totals
        net_revenues = LineItem(
            name="net_revenues",
            category="net_income",
            formula="rev1 + rev2 - exp1 - exp2",
        )

        # Intentionally shuffled order
        line_items = [net_revenues, exp1, rev1, exp2, rev2]

        model = Model(
            line_items=line_items, years=[2023, 2024], categories=basic_categories
        )

        matrix = generate_value_matrix(
            model.years,
            model._line_item_definitions + model.generators,
            model.category_metadata,
            model.line_item_metadata,
        )

        for year in [2023, 2024]:
            expected_revenue_total = rev1.values[year] + rev2.values[year]
            expected_expenses_total = exp1.values[year] + exp2.values[year]
            assert matrix[year]["rev1"] == rev1.values[year]
            assert matrix[year]["rev2"] == rev2.values[year]
            assert matrix[year]["exp1"] == exp1.values[year]
            assert matrix[year]["exp2"] == exp2.values[year]
            assert (
                matrix[year]["net_revenues"]
                == expected_revenue_total - expected_expenses_total
            )


class TestCalculateCategoryTotal:
    """Test cases for the _calculate_category_total() function."""

    def test_calculate_category_total_basic(self):
        """Test basic category total calculation with simple values."""
        values_by_name = {"revenue1": 1000.0, "revenue2": 500.0, "expense1": 300.0}

        metadata = [
            {"name": "revenue1", "source_type": "line_item", "category": "income"},
            {"name": "revenue2", "source_type": "line_item", "category": "income"},
            {"name": "expense1", "source_type": "line_item", "category": "expenses"},
        ]

        category_metadata = [
            {"name": "income"},
            {"name": "expenses"},
        ]

        # Test income category
        result = _calculate_category_total(
            values_by_name, metadata, "income", category_metadata
        )
        assert result == 1500.0

        # Test expenses category
        result = _calculate_category_total(
            values_by_name, metadata, "expenses", category_metadata
        )
        assert result == 300.0

    def test_calculate_category_total_with_none_values(self):
        """Test that None values are treated as 0 in calculations."""
        values_by_name = {"item1": 100.0, "item2": None, "item3": 200.0}

        metadata = [
            {"name": "item1", "source_type": "line_item", "category": "test_category"},
            {"name": "item2", "source_type": "line_item", "category": "test_category"},
            {"name": "item3", "source_type": "line_item", "category": "test_category"},
        ]

        category_metadata = [
            {"name": "test_category"},
        ]

        result = _calculate_category_total(
            values_by_name, metadata, "test_category", category_metadata
        )
        assert result == 300.0  # 100 + 0 + 200

    def test_calculate_category_total_empty_category(self):
        """Test calculation for a category with no line items."""
        values_by_name = {
            "item1": 100.0,
        }

        metadata = [
            {"name": "item1", "source_type": "line_item", "category": "income"},
            {"name": "total", "source_type": "category", "category": None},
        ]

        category_metadata = [
            {"name": "income"},
        ]

        # Test category that exists in category_metadata but has no line items in
        # this category
        with pytest.raises(
            KeyError, match="Category 'expenses' not found in category definitions"
        ):
            _calculate_category_total(
                values_by_name, metadata, "expenses", category_metadata
            )

    def test_calculate_category_total_invalid_category(self):
        """Test error handling for non-existent categories."""
        values_by_name = {"item1": 100.0}
        metadata = [{"name": "item1", "source_type": "line_item", "category": "income"}]
        category_metadata = [{"name": "income"}]

        with pytest.raises(KeyError) as exc_info:
            _calculate_category_total(
                values_by_name, metadata, "nonexistent", category_metadata
            )

        assert "Category 'nonexistent' not found in category definitions" in str(
            exc_info.value
        )
        assert "Available categories: ['income']" in str(exc_info.value)

    def test_calculate_category_total_missing_item_in_values(self):
        """Test error handling when line item is missing from values."""
        values_by_name = {"item1": 100.0}  # item2 is missing
        metadata = [
            {"name": "item1", "source_type": "line_item", "category": "income"},
            {"name": "item2", "source_type": "line_item", "category": "income"},
        ]
        category_metadata = [{"name": "income"}]

        with pytest.raises(KeyError) as exc_info:
            _calculate_category_total(
                values_by_name, metadata, "income", category_metadata
            )

        assert "Line item 'item2' in category 'income' not found in values" in str(
            exc_info.value
        )

    def test_calculate_category_total_mixed_metadata(self):
        """Test calculation with mixed metadata containing different source types."""
        values_by_name = {"revenue": 1000.0, "expenses": 600.0}

        metadata = [
            {"name": "revenue", "source_type": "line_item", "category": "income"},
            {"name": "expenses", "source_type": "line_item", "category": "income"},
            {"name": "total_income", "source_type": "category", "category": None},
            {"name": "assumption1", "source_type": "assumption", "category": "income"},
        ]
        category_metadata = [{"name": "income"}]

        # Should only sum line_item types
        result = _calculate_category_total(
            values_by_name, metadata, "income", category_metadata
        )
        assert result == 1600.0  # Only revenue + expenses

    def test_calculate_category_total_multiple_categories(self):
        """Test calculation with multiple categories in metadata."""
        values_by_name = {"rev1": 500.0, "rev2": 300.0, "exp1": 100.0, "exp2": 200.0}

        metadata = [
            {"name": "rev1", "source_type": "line_item", "category": "revenue"},
            {"name": "rev2", "source_type": "line_item", "category": "revenue"},
            {"name": "exp1", "source_type": "line_item", "category": "expenses"},
            {"name": "exp2", "source_type": "line_item", "category": "expenses"},
        ]
        category_metadata = [{"name": "revenue"}, {"name": "expenses"}]

        # Test revenue category
        revenue_total = _calculate_category_total(
            values_by_name, metadata, "revenue", category_metadata
        )
        assert revenue_total == 800.0

        # Test expenses category
        expenses_total = _calculate_category_total(
            values_by_name, metadata, "expenses", category_metadata
        )
        assert expenses_total == 300.0

    def test_calculate_category_total_zero_values(self):
        """Test calculation with zero values."""
        values_by_name = {"item1": 0.0, "item2": 100.0, "item3": 0.0}

        metadata = [
            {"name": "item1", "source_type": "line_item", "category": "test"},
            {"name": "item2", "source_type": "line_item", "category": "test"},
            {"name": "item3", "source_type": "line_item", "category": "test"},
        ]
        category_metadata = [{"name": "test"}]

        result = _calculate_category_total(
            values_by_name, metadata, "test", category_metadata
        )
        assert result == 100.0

    def test_calculate_category_total_negative_values(self):
        """Test calculation with negative values."""
        values_by_name = {"income": 1000.0, "loss": -200.0, "adjustment": -50.0}

        metadata = [
            {"name": "income", "source_type": "line_item", "category": "net_income"},
            {"name": "loss", "source_type": "line_item", "category": "net_income"},
            {
                "name": "adjustment",
                "source_type": "line_item",
                "category": "net_income",
            },
        ]
        category_metadata = [{"name": "net_income"}]

        result = _calculate_category_total(
            values_by_name, metadata, "net_income", category_metadata
        )
        assert result == 750.0  # 1000 + (-200) + (-50)

    def test_calculate_category_total_empty_metadata(self):
        """Test error handling with empty metadata."""
        values_by_name = {"item1": 100.0}
        metadata = []
        category_metadata = []

        with pytest.raises(KeyError) as exc_info:
            _calculate_category_total(
                values_by_name, metadata, "any_category", category_metadata
            )

        assert "Category 'any_category' not found in category definitions" in str(
            exc_info.value
        )
        assert "Available categories: []" in str(exc_info.value)


class TestParseCategoryTotalFormula:
    """Test cases for the _parse_category_total_formula() helper function."""

    def test_parse_category_total_basic(self):
        """Test parsing basic category_total formula without space."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        result = _parse_category_total_formula("category_total:revenue")
        assert result == "revenue"

    def test_parse_category_total_with_space(self):
        """Test parsing category_total formula with space after colon."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        result = _parse_category_total_formula("category_total: revenue")
        assert result == "revenue"

    def test_parse_category_total_with_multiple_spaces(self):
        """Test parsing category_total formula with multiple spaces after colon."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        result = _parse_category_total_formula("category_total:   expenses")
        assert result == "expenses"

    def test_parse_category_total_with_underscore_in_name(self):
        """Test parsing category_total formula with underscore in category name."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        result = _parse_category_total_formula("category_total:net_income")
        assert result == "net_income"

    def test_parse_category_total_not_matching(self):
        """Test that regular formulas return None."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        assert _parse_category_total_formula("revenue * 2") is None
        assert _parse_category_total_formula("revenue + expenses") is None
        assert _parse_category_total_formula("100") is None

    def test_parse_category_total_empty_string(self):
        """Test that empty string returns None."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        assert _parse_category_total_formula("") is None

    def test_parse_category_total_none(self):
        """Test that None returns None."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        assert _parse_category_total_formula(None) is None

    def test_parse_category_total_with_extra_text(self):
        """Test that formulas with extra text don't match."""
        from pyproforma.models.model.value_matrix import _parse_category_total_formula

        assert _parse_category_total_formula("category_total:revenue + 100") is None
        assert _parse_category_total_formula("2 * category_total:revenue") is None


class TestCategoryTotalFormula:
    """Test cases for using category_total:category_name in formulas."""

    @pytest.fixture
    def basic_categories(self):
        """Create basic categories for testing."""
        return [
            Category(name="revenue", label="Revenue"),
            Category(name="expenses", label="Expenses"),
            Category(name="summary", label="Summary"),
        ]

    def test_category_total_formula_basic(self, basic_categories):
        """Test basic category_total formula usage."""
        revenue1 = LineItem(
            name="revenue1", category="revenue", values={2023: 1000, 2024: 1200}
        )
        revenue2 = LineItem(
            name="revenue2", category="revenue", values={2023: 500, 2024: 600}
        )
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )

        model = Model(
            line_items=[revenue1, revenue2, total_revenue],
            years=[2023, 2024],
            categories=basic_categories,
        )

        # Check that the total is calculated correctly
        assert model.value("total_revenue", 2023) == 1500
        assert model.value("total_revenue", 2024) == 1800

    def test_category_total_formula_with_space(self, basic_categories):
        """Test category_total formula with space after colon."""
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        revenue2 = LineItem(name="revenue2", category="revenue", values={2023: 500})
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total: revenue"
        )

        model = Model(
            line_items=[revenue1, revenue2, total_revenue],
            years=[2023],
            categories=basic_categories,
        )

        assert model.value("total_revenue", 2023) == 1500

    def test_category_total_formula_with_none_values(self, basic_categories):
        """Test that None values are treated as 0 in category_total formula."""
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        revenue2 = LineItem(name="revenue2", category="revenue", values={2023: None})
        revenue3 = LineItem(name="revenue3", category="revenue", values={2023: 500})
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )

        model = Model(
            line_items=[revenue1, revenue2, revenue3, total_revenue],
            years=[2023],
            categories=basic_categories,
        )

        # None should be treated as 0
        assert model.value("total_revenue", 2023) == 1500

    def test_category_total_formula_order_independent(self, basic_categories):
        """Test that category_total formula works regardless of line item order."""
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        revenue2 = LineItem(name="revenue2", category="revenue", values={2023: 500})
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )

        # Test with total_revenue first
        model1 = Model(
            line_items=[total_revenue, revenue1, revenue2],
            years=[2023],
            categories=basic_categories,
        )

        # Test with total_revenue last
        model2 = Model(
            line_items=[revenue1, revenue2, total_revenue],
            years=[2023],
            categories=basic_categories,
        )

        # Test with total_revenue in the middle
        model3 = Model(
            line_items=[revenue1, total_revenue, revenue2],
            years=[2023],
            categories=basic_categories,
        )

        assert model1.value("total_revenue", 2023) == 1500
        assert model2.value("total_revenue", 2023) == 1500
        assert model3.value("total_revenue", 2023) == 1500

    def test_category_total_formula_empty_category(self, basic_categories):
        """Test category_total formula with empty category."""
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )

        model = Model(
            line_items=[total_revenue],
            years=[2023],
            categories=basic_categories,
        )

        # Empty category should sum to 0
        assert model.value("total_revenue", 2023) == 0

    def test_category_total_formula_invalid_category(self, basic_categories):
        """Test that invalid category raises error."""
        total = LineItem(
            name="total", category="summary", formula="category_total:nonexistent"
        )

        with pytest.raises(KeyError, match="Category 'nonexistent' not found"):
            Model(
                line_items=[total],
                years=[2023],
                categories=basic_categories,
            )

    def test_category_total_formula_with_multiple_categories(self, basic_categories):
        """Test using category_total formulas for multiple categories."""
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        revenue2 = LineItem(name="revenue2", category="revenue", values={2023: 500})
        expense1 = LineItem(name="expense1", category="expenses", values={2023: 300})
        expense2 = LineItem(name="expense2", category="expenses", values={2023: 200})
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )
        total_expenses = LineItem(
            name="total_expenses", category="summary", formula="category_total:expenses"
        )

        model = Model(
            line_items=[
                revenue1,
                revenue2,
                expense1,
                expense2,
                total_revenue,
                total_expenses,
            ],
            years=[2023],
            categories=basic_categories,
        )

        assert model.value("total_revenue", 2023) == 1500
        assert model.value("total_expenses", 2023) == 500

    def test_category_total_formula_does_not_use_evaluate(self, basic_categories):
        """Test that category_total formula does not use regular evaluate()."""
        # This tests that the category_total pattern takes precedence over evaluate()
        # If we tried to use evaluate() with "category_total:revenue", it would fail
        revenue1 = LineItem(name="revenue1", category="revenue", values={2023: 1000})
        total_revenue = LineItem(
            name="total_revenue", category="summary", formula="category_total:revenue"
        )

        model = Model(
            line_items=[revenue1, total_revenue],
            years=[2023],
            categories=basic_categories,
        )

        # Should work without error - this would fail if it tried to use evaluate()
        assert model.value("total_revenue", 2023) == 1000
