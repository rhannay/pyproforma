import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.constraint import Constraint
from pyproforma.models.generator.debt import Debt


class TestGetItemMetadata:
    """Test the _get_item_metadata method of the Model class."""

    @pytest.fixture
    def basic_model(self):
        """Create a basic model for testing."""
        line_items = [
            LineItem(
                name="revenue",
                label="Revenue",
                category="income",
                values={2023: 100000, 2024: 120000},
                value_format="currency",
            ),
            LineItem(
                name="expenses",
                label="Expenses",
                category="costs",
                formula="revenue * 0.6",
                value_format="currency",
            ),
        ]
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]
        return Model(
            line_items=line_items,
            categories=categories,
            years=[2023, 2024],
        )

    @pytest.fixture
    def model_with_multi_line_items(self):
        """Create a model with multi line items for testing."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
        ]
        multi_line_items = [
            Debt(
                name="debt_schedule",
                par_amount={2023: 50000},
                interest_rate=0.05,
                term=5,
            )
        ]
        return Model(
            line_items=line_items,
            generators=multi_line_items,
            years=[2023, 2024, 2025],
        )

    def test_get_item_metadata_valid_line_item(self, basic_model):
        """Test getting metadata for a valid line item."""
        metadata = basic_model._get_item_metadata("revenue")

        assert metadata["name"] == "revenue"
        assert metadata["label"] == "Revenue"
        assert metadata["value_format"] == "currency"
        assert metadata["source_type"] == "line_item"
        assert metadata["source_name"] == "revenue"

    def test_get_item_metadata_valid_formula_item(self, basic_model):
        """Test getting metadata for a line item with formula."""
        metadata = basic_model._get_item_metadata("expenses")

        assert metadata["name"] == "expenses"
        assert metadata["label"] == "Expenses"
        assert metadata["value_format"] == "currency"
        assert metadata["source_type"] == "line_item"
        assert metadata["source_name"] == "expenses"

    def test_get_item_metadata_generator_output(
        self, model_with_multi_line_items
    ):
        """Test that generator fields are not in line_item_metadata."""
        # Generators no longer add items to line_item_metadata
        debt_items = [
            item
            for item in model_with_multi_line_items.line_item_metadata
            if item["source_type"] == "generator"
        ]

        # Should be empty since generators don't add to line_item_metadata anymore
        assert len(debt_items) == 0
        
        # Instead, generator fields should be accessible via generator() method
        # Verify the generator exists
        assert len(model_with_multi_line_items.generators) > 0
        generator_name = model_with_multi_line_items.generators[0].name
        gen_results = model_with_multi_line_items.generator(generator_name)
        assert len(gen_results.field_names) > 0

    def test_get_item_metadata_invalid_name_raises_error(self, basic_model):
        """Test that getting metadata for invalid item raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            basic_model._get_item_metadata("nonexistent_item")

        assert "Item 'nonexistent_item' not found in model" in str(excinfo.value)

    def test_get_item_metadata_empty_model(self):
        """Test getting metadata from an empty model."""
        empty_model = Model()

        with pytest.raises(KeyError) as excinfo:
            empty_model._get_item_metadata("any_item")

        assert "Item 'any_item' not found in model" in str(excinfo.value)

    def test_get_item_metadata_case_sensitive(self, basic_model):
        """Test that item metadata lookup is case sensitive."""
        # Should work with correct case
        metadata = basic_model._get_item_metadata("revenue")
        assert metadata["name"] == "revenue"

        # Should fail with incorrect case
        with pytest.raises(KeyError):
            basic_model._get_item_metadata("Revenue")

        with pytest.raises(KeyError):
            basic_model._get_item_metadata("REVENUE")

    def test_get_item_metadata_whitespace_sensitive(self, basic_model):
        """Test that item metadata lookup is whitespace sensitive."""
        # Should work without whitespace
        metadata = basic_model._get_item_metadata("revenue")
        assert metadata["name"] == "revenue"

        # Should fail with whitespace
        with pytest.raises(KeyError):
            basic_model._get_item_metadata(" revenue")

        with pytest.raises(KeyError):
            basic_model._get_item_metadata("revenue ")


class TestGetCategoryMetadata:
    """Test the _get_category_metadata method of the Model class."""

    @pytest.fixture
    def basic_model(self):
        """Create a basic model for testing."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
            LineItem(name="salary", category="expenses", values={2023: 50000}),
            LineItem(name="rent", category="expenses", values={2023: 20000}),
        ]
        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Operating Expenses"),
            Category(name="assets", label="Assets"),
        ]
        return Model(
            line_items=line_items,
            categories=categories,
            years=[2023, 2024],
        )

    @pytest.fixture
    def model_with_multi_line_items(self):
        """Create a model with multi line items for testing."""
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000}),
        ]
        multi_line_items = [
            Debt(
                name="debt_schedule",
                par_amount={2023: 50000},
                interest_rate=0.05,
                term=5,
            )
        ]
        return Model(
            line_items=line_items,
            generators=multi_line_items,
            years=[2023, 2024, 2025],
        )

    def test_get_category_metadata_valid_category(self, basic_model):
        """Test getting metadata for a valid category."""
        metadata = basic_model._get_category_metadata("income")

        assert metadata["name"] == "income"
        assert metadata["label"] == "Income"

    def test_get_category_metadata_category_without_total(self, basic_model):
        """Test getting metadata for a category without totals."""
        metadata = basic_model._get_category_metadata("assets")

        assert metadata["name"] == "assets"
        assert metadata["label"] == "Assets"

    def test_get_category_metadata_auto_generated_category(self):
        """Test getting metadata for auto-generated categories."""
        # Create model with auto-inferred categories
        line_items = [
            LineItem(name="revenue", category="sales", values={2023: 100000}),
            LineItem(name="costs", category="expenses", values={2023: 50000}),
        ]
        model = Model(line_items=line_items, years=[2023])

        # Auto-generated categories should have name == label
        sales_metadata = model._get_category_metadata("sales")
        assert sales_metadata["name"] == "sales"
        assert sales_metadata["label"] == "sales"

        expenses_metadata = model._get_category_metadata("expenses")
        assert expenses_metadata["name"] == "expenses"
        assert expenses_metadata["label"] == "expenses"

    def test_get_category_metadata_with_multi_line_items(
        self, model_with_multi_line_items
    ):
        """Test getting category metadata when multi line items create categories."""
        # The debt multi line item should create debt schedule categories
        # Let's check what categories actually exist
        available_categories = [
            cat["name"] for cat in model_with_multi_line_items.category_metadata
        ]

        # Should have at least the income category from our line item
        assert "income" in available_categories

        # Test getting metadata for the income category
        metadata = model_with_multi_line_items._get_category_metadata("income")
        assert metadata["name"] == "income"
        # Should have appropriate metadata structure
        assert "label" in metadata

    def test_get_category_metadata_invalid_name_raises_error(self, basic_model):
        """Test that getting metadata for invalid category raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            basic_model._get_category_metadata("nonexistent_category")

        error_message = str(excinfo.value)
        assert "Category 'nonexistent_category' not found in model" in error_message
        assert "Available categories:" in error_message

    def test_get_category_metadata_error_message_includes_available_categories(
        self, basic_model
    ):
        """Test that error message includes list of available categories."""
        with pytest.raises(KeyError) as excinfo:
            basic_model._get_category_metadata("invalid")

        error_message = str(excinfo.value)
        assert "income" in error_message
        assert "expenses" in error_message
        assert "assets" in error_message

    def test_get_category_metadata_empty_model(self):
        """Test getting category metadata from an empty model."""
        empty_model = Model()

        with pytest.raises(KeyError) as excinfo:
            empty_model._get_category_metadata("any_category")

        assert "Category 'any_category' not found in model" in str(excinfo.value)

    def test_get_category_metadata_case_sensitive(self, basic_model):
        """Test that category metadata lookup is case sensitive."""
        # Should work with correct case
        metadata = basic_model._get_category_metadata("income")
        assert metadata["name"] == "income"

        # Should fail with incorrect case
        with pytest.raises(KeyError):
            basic_model._get_category_metadata("Income")

        with pytest.raises(KeyError):
            basic_model._get_category_metadata("INCOME")

    def test_get_category_metadata_whitespace_sensitive(self, basic_model):
        """Test that category metadata lookup is whitespace sensitive."""
        # Should work without whitespace
        metadata = basic_model._get_category_metadata("income")
        assert metadata["name"] == "income"

        # Should fail with whitespace
        with pytest.raises(KeyError):
            basic_model._get_category_metadata(" income")

        with pytest.raises(KeyError):
            basic_model._get_category_metadata("income ")


class TestGetConstraintMetadata:
    """Test the _get_constraint_metadata method of the Model class."""

    @pytest.fixture
    def basic_line_items(self):
        """Create basic line items for testing."""
        return [
            LineItem(
                name="revenue", category="income", values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses", category="costs", values={2023: 50000, 2024: 60000}
            ),
            LineItem(name="profit", category="income", formula="revenue - expenses"),
        ]

    @pytest.fixture
    def basic_constraints(self):
        """Create basic constraints for testing."""
        return [
            Constraint(
                name="revenue_minimum",
                line_item_name="revenue",
                target=80000,
                operator="ge",
                tolerance=1000,
            ),
            Constraint(
                name="expense_ratio",
                line_item_name="expenses",
                target={2023: 50000, 2024: 55000},
                operator="le",
            ),
            Constraint(
                name="profit_target",
                line_item_name="profit",
                target=50000,
                operator="eq",
                tolerance=5000,
            ),
        ]

    @pytest.fixture
    def model_with_constraints(self, basic_line_items, basic_constraints):
        """Create a model with constraints for testing."""
        return Model(
            line_items=basic_line_items,
            constraints=basic_constraints,
            years=[2023, 2024],
        )

    def test_get_constraint_metadata_valid_constraint(self, model_with_constraints):
        """Test getting metadata for a valid constraint."""
        metadata = model_with_constraints._get_constraint_metadata("revenue_minimum")

        assert metadata["name"] == "revenue_minimum"
        assert metadata["label"] == "revenue_minimum"
        assert metadata["line_item_name"] == "revenue"
        assert metadata["target"] == 80000
        assert metadata["operator"] == "ge"
        assert metadata["operator_symbol"] == ">="
        assert metadata["tolerance"] == 1000

    def test_get_constraint_metadata_constraint_with_dict_target(
        self, model_with_constraints
    ):
        """Test getting metadata for constraint with dictionary target."""
        metadata = model_with_constraints._get_constraint_metadata("expense_ratio")

        assert metadata["name"] == "expense_ratio"
        assert metadata["line_item_name"] == "expenses"
        assert metadata["target"] == {2023: 50000, 2024: 55000}
        assert metadata["operator"] == "le"
        assert metadata["operator_symbol"] == "<="
        assert metadata["tolerance"] == 0.0  # Default tolerance

    def test_get_constraint_metadata_constraint_with_tolerance(
        self, model_with_constraints
    ):
        """Test getting metadata for constraint with custom tolerance."""
        metadata = model_with_constraints._get_constraint_metadata("profit_target")

        assert metadata["name"] == "profit_target"
        assert metadata["line_item_name"] == "profit"
        assert metadata["target"] == 50000
        assert metadata["operator"] == "eq"
        assert metadata["operator_symbol"] == "="
        assert metadata["tolerance"] == 5000

    def test_get_constraint_metadata_all_operators(self):
        """Test getting metadata for constraints with different operators."""
        line_items = [LineItem(name="value", category="test", values={2023: 100})]

        operators_tests = [
            ("eq", "="),
            ("ne", "!="),
            ("lt", "<"),
            ("le", "<="),
            ("gt", ">"),
            ("ge", ">="),
        ]

        for operator, symbol in operators_tests:
            constraint = Constraint(
                name=f"test_{operator}",
                line_item_name="value",
                target=100,
                operator=operator,
            )
            model = Model(
                line_items=line_items,
                constraints=[constraint],
                years=[2023],
            )

            metadata = model._get_constraint_metadata(f"test_{operator}")
            assert metadata["operator"] == operator
            assert metadata["operator_symbol"] == symbol

    def test_get_constraint_metadata_invalid_name_raises_error(
        self, model_with_constraints
    ):
        """Test that getting metadata for invalid constraint raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            model_with_constraints._get_constraint_metadata("nonexistent_constraint")

        error_message = str(excinfo.value)
        assert "Constraint 'nonexistent_constraint' not found in model" in error_message
        assert "Available constraints:" in error_message

    def test_get_constraint_metadata_error_message_includes_available_constraints(
        self, model_with_constraints
    ):
        """Test that error message includes list of available constraints."""
        with pytest.raises(KeyError) as excinfo:
            model_with_constraints._get_constraint_metadata("invalid")

        error_message = str(excinfo.value)
        assert "revenue_minimum" in error_message
        assert "expense_ratio" in error_message
        assert "profit_target" in error_message

    def test_get_constraint_metadata_model_with_no_constraints(self):
        """Test getting constraint metadata from model with no constraints."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 100})]
        model = Model(line_items=line_items, years=[2023])

        with pytest.raises(KeyError) as excinfo:
            model._get_constraint_metadata("any_constraint")

        assert "Constraint 'any_constraint' not found in model" in str(excinfo.value)
        assert "Available constraints: []" in str(excinfo.value)

    def test_get_constraint_metadata_empty_model(self):
        """Test getting constraint metadata from an empty model."""
        empty_model = Model()

        with pytest.raises(KeyError) as excinfo:
            empty_model._get_constraint_metadata("any_constraint")

        assert "Constraint 'any_constraint' not found in model" in str(excinfo.value)

    def test_get_constraint_metadata_case_sensitive(self, model_with_constraints):
        """Test that constraint metadata lookup is case sensitive."""
        # Should work with correct case
        metadata = model_with_constraints._get_constraint_metadata("revenue_minimum")
        assert metadata["name"] == "revenue_minimum"

        # Should fail with incorrect case
        with pytest.raises(KeyError):
            model_with_constraints._get_constraint_metadata("Revenue_Minimum")

        with pytest.raises(KeyError):
            model_with_constraints._get_constraint_metadata("REVENUE_MINIMUM")

    def test_get_constraint_metadata_whitespace_sensitive(self, model_with_constraints):
        """Test that constraint metadata lookup is whitespace sensitive."""
        # Should work without whitespace
        metadata = model_with_constraints._get_constraint_metadata("revenue_minimum")
        assert metadata["name"] == "revenue_minimum"

        # Should fail with whitespace
        with pytest.raises(KeyError):
            model_with_constraints._get_constraint_metadata(" revenue_minimum")

        with pytest.raises(KeyError):
            model_with_constraints._get_constraint_metadata("revenue_minimum ")

    def test_get_constraint_metadata_returns_constraint_object_metadata(
        self, model_with_constraints
    ):
        """Test that the metadata contains the expected constraint object properties."""
        metadata = model_with_constraints._get_constraint_metadata("revenue_minimum")

        # Verify all expected fields are present
        expected_fields = [
            "name",
            "label",
            "line_item_name",
            "target",
            "operator",
            "operator_symbol",
            "tolerance",
        ]
        for field in expected_fields:
            assert field in metadata, f"Field '{field}' should be in metadata"

    def test_get_constraint_metadata_with_custom_label(self):
        """Test getting metadata for constraint with custom label."""
        line_items = [LineItem(name="revenue", category="income", values={2023: 100})]
        constraint = Constraint(
            name="revenue_check",
            label="Revenue Validation Check",
            line_item_name="revenue",
            target=100,
            operator="eq",
        )
        model = Model(
            line_items=line_items,
            constraints=[constraint],
            years=[2023],
        )

        metadata = model._get_constraint_metadata("revenue_check")
        assert metadata["name"] == "revenue_check"
        assert metadata["label"] == "Revenue Validation Check"
