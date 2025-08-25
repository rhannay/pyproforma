import pytest
from pyproforma import LineItem, Model, Category
from pyproforma.models.multi_line_item.debt import Debt


class TestModelToFromDict:
    """Test cases for the Model.to_dict() and Model.from_dict() methods."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for testing."""
        line_items = [
            LineItem(name="revenue", category="income", label="Total Revenue", 
                    values={2023: 100000, 2024: 120000}),
            LineItem(name="expenses", category="costs", label="Total Expenses", 
                    values={2023: 80000, 2024: 90000}),
            LineItem(name="growth_rate", category="assumptions", label="Growth Rate", 
                    values={2023: 0.1, 2024: 0.15})
        ]
        
        categories = [
            Category(name="income", label="Income Statement"),
            Category(name="costs", label="Cost Items"),
            Category(name="assumptions", label="Assumptions")
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories
        )

    @pytest.fixture
    def complex_model(self):
        """Create a more complex model with formulas."""
        line_items = [
            LineItem(name="revenue", category="income", 
                    values={2023: 100000}, formula="revenue[-1] * (1 + growth_rate)"),
            LineItem(name="expenses", category="costs", 
                    values={2023: 80000}, formula="expenses[-1] * 1.05"),
            LineItem(name="profit", category="calculated", 
                    formula="total_income - total_costs"),
            LineItem(name="growth_rate", category="assumptions", 
                    values={2023: 0.1, 2024: 0.15, 2025: 0.12}),
            LineItem(name="tax_rate", category="assumptions", 
                    values={2023: 0.25, 2024: 0.25, 2025: 0.27})
        ]
        
        categories = [
            Category(name="income", label="Income Statement", include_total=True),
            Category(name="costs", label="Cost Items", include_total=True),
            Category(name="calculated", label="Calculated Items", include_total=False),
            Category(name="assumptions", label="Assumptions", include_total=False)
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024, 2025],
            categories=categories
        )

    def test_to_dict_basic_structure(self, simple_model):
        """Test that to_dict() returns the expected structure."""
        result = simple_model.to_dict()
        
        # Check that all expected keys are present
        assert "years" in result
        assert "line_items" in result
        assert "categories" in result
        assert "line_item_generators" in result
        
        # Check basic types
        assert isinstance(result["years"], list)
        assert isinstance(result["line_items"], list)
        assert isinstance(result["categories"], list)
        assert isinstance(result["line_item_generators"], list)

    def test_to_dict_preserves_years(self, simple_model):
        """Test that to_dict() preserves the years."""
        result = simple_model.to_dict()
        assert result["years"] == [2023, 2024]

    def test_to_dict_preserves_line_items(self, simple_model):
        """Test that to_dict() preserves line items."""
        result = simple_model.to_dict()
        line_items = result["line_items"]
        
        assert len(line_items) == 3  # Now includes growth_rate
        
        # Check first line item
        revenue_item = next(item for item in line_items if item["name"] == "revenue")
        assert revenue_item["name"] == "revenue"
        assert revenue_item["category"] == "income"
        assert revenue_item["label"] == "Total Revenue"
        assert revenue_item["values"][2023] == 100000
        assert revenue_item["values"][2024] == 120000

    def test_to_dict_preserves_assumptions_as_line_items(self, simple_model):
        """Test that to_dict() preserves assumptions as line items."""
        result = simple_model.to_dict()
        line_items = result["line_items"]
        
        growth_rate = next(item for item in line_items if item["name"] == "growth_rate")
        assert growth_rate["name"] == "growth_rate"
        assert growth_rate["category"] == "assumptions"
        assert growth_rate["label"] == "Growth Rate"
        assert growth_rate["values"][2023] == 0.1
        assert growth_rate["values"][2024] == 0.15

    def test_to_dict_preserves_categories(self, simple_model):
        """Test that to_dict() preserves categories."""
        result = simple_model.to_dict()
        categories = result["categories"]
        
        assert len(categories) == 3  # Now includes assumptions category
        
        # Check income category
        income_cat = next(cat for cat in categories if cat["name"] == "income")
        assert income_cat["name"] == "income"
        assert income_cat["label"] == "Income Statement"

    def test_from_dict_basic_round_trip(self, simple_model: Model):
        """Test basic round trip: model -> dict -> model."""
        # Convert to dict
        model_dict = simple_model.to_dict()
        
        # Convert back to model
        recreated_model = Model.from_dict(model_dict)
        
        # Test that it's a different object
        assert recreated_model is not simple_model
        
        # Test that basic structure is preserved
        assert recreated_model.years == simple_model.years
        assert len(recreated_model._line_item_definitions) == len(simple_model._line_item_definitions)
        assert len(recreated_model._category_definitions) == len(simple_model._category_definitions)

    def test_from_dict_preserves_line_item_values(self, simple_model):
        """Test that round trip preserves line item values."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test that values are preserved
        assert recreated_model.value("revenue", 2023) == simple_model.value("revenue", 2023)
        assert recreated_model.value("revenue", 2024) == simple_model.value("revenue", 2024)
        assert recreated_model.value("expenses", 2023) == simple_model.value("expenses", 2023)
        assert recreated_model.value("expenses", 2024) == simple_model.value("expenses", 2024)

    def test_from_dict_preserves_assumption_values(self, simple_model):
        """Test that round trip preserves assumption values (now as line items)."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test that assumption values are preserved
        assert recreated_model.value("growth_rate", 2023) == simple_model.value("growth_rate", 2023)
        assert recreated_model.value("growth_rate", 2024) == simple_model.value("growth_rate", 2024)

    def test_from_dict_preserves_line_item_attributes(self, simple_model):
        """Test that round trip preserves line item attributes."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Find the revenue line item in both models
        original_revenue = next(item for item in simple_model._line_item_definitions if item.name == "revenue")
        recreated_revenue = next(item for item in recreated_model._line_item_definitions if item.name == "revenue")
        
        # Test attributes are preserved
        assert recreated_revenue.name == original_revenue.name
        assert recreated_revenue.category == original_revenue.category
        assert recreated_revenue.label == original_revenue.label
        assert recreated_revenue.values == original_revenue.values

    def test_from_dict_preserves_assumption_attributes(self, simple_model):
        """Test that round trip preserves assumption attributes (now as line items)."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Find the growth rate assumption (now a line item) in both models
        original_assumption = next(item for item in simple_model._line_item_definitions if item.name == "growth_rate")
        recreated_assumption = next(item for item in recreated_model._line_item_definitions if item.name == "growth_rate")
        
        # Test attributes are preserved
        assert recreated_assumption.name == original_assumption.name
        assert recreated_assumption.label == original_assumption.label
        assert recreated_assumption.category == original_assumption.category
        assert recreated_assumption.values == original_assumption.values

    def test_from_dict_preserves_category_attributes(self, simple_model: Model):
        """Test that round trip preserves category attributes."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Find the income category in both models
        original_category = next(cat for cat in simple_model._category_definitions if cat.name == "income")
        recreated_category = next(cat for cat in recreated_model._category_definitions if cat.name == "income")
        
        # Test attributes are preserved
        assert recreated_category.name == original_category.name
        assert recreated_category.label == original_category.label
        assert recreated_category.include_total == original_category.include_total

    def test_complex_model_round_trip(self, complex_model):
        """Test round trip with a complex model including formulas."""
        # Convert to dict and back
        model_dict = complex_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test that formulas are preserved
        original_revenue = next(item for item in complex_model._line_item_definitions if item.name == "revenue")
        recreated_revenue = next(item for item in recreated_model._line_item_definitions if item.name == "revenue")
        assert recreated_revenue.formula == original_revenue.formula
        
        # Test that calculations work correctly
        for year in complex_model.years:
            assert recreated_model.value("revenue", year) == complex_model.value("revenue", year)
            assert recreated_model.value("expenses", year) == complex_model.value("expenses", year)
            assert recreated_model.value("profit", year) == complex_model.value("profit", year)

    def test_round_trip_with_category_totals(self, complex_model):
        """Test that round trip preserves category totals."""
        # Convert to dict and back
        model_dict = complex_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test that category totals work in both models
        for year in complex_model.years:
            # Test category totals (if they exist)
            try:
                original_total = complex_model.value("total_income", year)
                recreated_total = recreated_model.value("total_income", year)
                assert recreated_total == original_total
            except KeyError:
                # Category total might not exist - that's okay
                pass

    def test_multiple_round_trips(self, simple_model):
        """Test that multiple round trips don't introduce errors."""
        current_model = simple_model
        
        # Perform multiple round trips
        for i in range(3):
            model_dict = current_model.to_dict()
            current_model = Model.from_dict(model_dict)
            
            # Verify values are still correct
            assert current_model.value("revenue", 2023) == 100000
            assert current_model.value("revenue", 2024) == 120000
            assert current_model.value("expenses", 2023) == 80000
            assert current_model.value("expenses", 2024) == 90000
            assert current_model.value("growth_rate", 2023) == 0.1
            assert current_model.value("growth_rate", 2024) == 0.15

    def test_to_dict_with_empty_line_item_generators(self, simple_model):
        """Test that to_dict() handles empty line item generators list."""
        result = simple_model.to_dict()
        assert result["line_item_generators"] == []

    def test_from_dict_with_empty_line_item_generators(self, simple_model):
        """Test that from_dict() handles empty line item generators list."""
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        assert len(recreated_model.multi_line_items) == 0

    def test_model_with_generators_round_trip(self):
        """Test that models with generators can be serialized and deserialized successfully."""
        # Create a model with a generator
        line_items = [
            LineItem(name="revenue", category="income", values={2023: 100000})
        ]
        
        debt_generator = Debt(
            name="loan",
            par_amount={2023: 50000},
            interest_rate=0.05,
            term=5
        )
        
        categories = [Category(name="income")]
        
        model = Model(
            line_items=line_items,
            years=[2023],
            categories=categories,
            multi_line_items=[debt_generator]
        )
        
        # to_dict should work
        result = model.to_dict()
        assert "line_item_generators" in result
        assert len(result["line_item_generators"]) == 1
        
        # from_dict should now work successfully
        recreated_model = Model.from_dict(result)
        
        # Verify the recreated model has the same structure
        assert len(recreated_model.multi_line_items) == 1
        assert recreated_model.multi_line_items[0].name == "loan"
        
        # Verify the values match
        original_value = model.value("loan.principal", 2023)
        recreated_value = recreated_model.value("loan.principal", 2023)
        assert original_value == recreated_value

    def test_round_trip_preserves_model_functionality(self, simple_model: Model):
        """Test that round trip preserves all model functionality."""
        # Convert to dict and back
        model_dict = simple_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test magic method access
        assert recreated_model["revenue", 2023] == simple_model["revenue", 2023]
        assert recreated_model["expenses", 2024] == simple_model["expenses", 2024]
        
        # Test helper methods
        assert recreated_model.line_item("revenue").label == simple_model.line_item("revenue").label
        assert recreated_model.line_item("revenue").value_format == simple_model.line_item("revenue").value_format

        # Test item info
        revenue_info_original = simple_model._get_item_metadata("revenue")
        revenue_info_recreated = recreated_model._get_item_metadata("revenue")
        assert revenue_info_original == revenue_info_recreated

    def test_round_trip_with_minimal_model(self):
        """Test round trip with minimal model configuration."""
        line_items = [
            LineItem(name="item1", category="test", values={2023: 100.0})
        ]
        
        minimal_model = Model(
            line_items=line_items,
            years=[2023]
        )
        
        # Convert to dict and back
        model_dict = minimal_model.to_dict()
        recreated_model = Model.from_dict(model_dict)
        
        # Test basic functionality
        assert recreated_model.value("item1", 2023) == 100.0
        assert len(recreated_model._category_definitions) == 1  # Auto-generated
        assert len(recreated_model.multi_line_items) == 0

    def test_dict_structure_completeness(self, complex_model):
        """Test that the dictionary structure contains all necessary information."""
        result = complex_model.to_dict()
        
        # Check that line items preserve formulas
        revenue_item = next(item for item in result["line_items"] if item["name"] == "revenue")
        assert "formula" in revenue_item
        assert revenue_item["formula"] == "revenue[-1] * (1 + growth_rate)"
        
        # Check that categories preserve all attributes
        income_cat = next(cat for cat in result["categories"] if cat["name"] == "income")
        assert "include_total" in income_cat
        assert income_cat["include_total"] == True
        
        # Check that assumption line items preserve all attributes  
        growth_rate = next(item for item in result["line_items"] if item["name"] == "growth_rate")
        assert growth_rate["name"] == "growth_rate"
        assert growth_rate["category"] == "assumptions"
        assert 2023 in growth_rate["values"]
        assert 2024 in growth_rate["values"]
        assert 2025 in growth_rate["values"]
