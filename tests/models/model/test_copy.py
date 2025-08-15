import pytest
from pyproforma import LineItem, Model, Category


class TestModelCopy:
    """Test cases for the Model.copy() method."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple model for testing."""
        line_items = [
            LineItem(name="revenue", category="income", label="Total Revenue", 
                    values={2023: 100.0, 2024: 120.0}),
            LineItem(name="expenses", category="costs", label="Total Expenses", 
                    values={2023: 80.0, 2024: 90.0}),
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
        """Create a more complex model with formulas and generators."""
        line_items = [
            LineItem(name="revenue", category="income", 
                    values={2023: 100.0}, formula="revenue[-1] * (1 + growth_rate)"),
            LineItem(name="expenses", category="costs", 
                    values={2023: 80.0}, formula="expenses[-1] * 1.05"),
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

    def test_copy_returns_model_instance(self, simple_model):
        """Test that copy() returns a Model instance."""
        copied = simple_model.copy()
        assert isinstance(copied, Model)

    def test_copy_creates_different_object(self, simple_model):
        """Test that copy() creates a different object reference."""
        copied = simple_model.copy()
        assert copied is not simple_model

    def test_copy_preserves_years(self, simple_model):
        """Test that copy() preserves the years list."""
        copied = simple_model.copy()
        assert copied.years == simple_model.years
        assert copied.years is not simple_model.years  # Different object

    def test_copy_preserves_line_items(self, simple_model):
        """Test that copy() preserves line items with deep copying."""
        copied = simple_model.copy()
        
        # Check counts and names are preserved
        assert len(copied._line_item_definitions) == len(simple_model._line_item_definitions)
        original_names = [item.name for item in simple_model._line_item_definitions]
        copied_names = [item.name for item in copied._line_item_definitions]
        assert copied_names == original_names
        
        # Check they are different objects
        assert copied._line_item_definitions is not simple_model._line_item_definitions
        for i in range(len(copied._line_item_definitions)):
            assert copied._line_item_definitions[i] is not simple_model._line_item_definitions[i]

    def test_copy_preserves_categories(self, simple_model):
        """Test that copy() preserves categories with deep copying."""
        copied: Model = simple_model.copy()
        
        # Check counts and names are preserved
        assert len(copied._category_definitions) == len(simple_model._category_definitions)
        original_names = [cat.name for cat in simple_model._category_definitions]
        copied_names = [cat.name for cat in copied._category_definitions]
        assert copied_names == original_names
        
        # Check they are different objects
        assert copied._category_definitions is not simple_model._category_definitions
        for i in range(len(copied._category_definitions)):
            assert copied._category_definitions[i] is not simple_model._category_definitions[i]

    def test_copy_preserves_values(self, simple_model):
        """Test that copy() preserves all calculated values."""
        copied = simple_model.copy()
        
        # Test that all values are accessible and identical
        for year in simple_model.years:
            assert copied.get_value("revenue", year) == simple_model.get_value("revenue", year)
            assert copied.get_value("expenses", year) == simple_model.get_value("expenses", year)
            assert copied.get_value("growth_rate", year) == simple_model.get_value("growth_rate", year)

    def test_copy_preserves_value_matrix(self, simple_model):
        """Test that copy() creates a new value matrix with identical values."""
        copied = simple_model.copy()
        
        # Value matrices should be different objects
        assert copied._value_matrix is not simple_model._value_matrix
        
        # But should contain the same values
        for year in simple_model.years:
            assert copied._value_matrix[year] is not simple_model._value_matrix[year]
            for name in simple_model._value_matrix[year]:
                assert copied._value_matrix[year][name] == simple_model._value_matrix[year][name]

    def test_copy_preserves_defined_names(self, simple_model):
        """Test that copy() preserves the defined names structure."""
        copied = simple_model.copy()
        
        # Should be different objects
        assert copied.defined_names_metadata is not simple_model.defined_names_metadata
        
        # Should have same content
        assert len(copied.defined_names_metadata) == len(simple_model.defined_names_metadata)
        
        # Check each defined name entry
        original_names = {item['name']: item for item in simple_model.defined_names_metadata}
        copied_names = {item['name']: item for item in copied.defined_names_metadata}
        
        assert set(original_names.keys()) == set(copied_names.keys())
        for name in original_names:
            assert original_names[name]['source_type'] == copied_names[name]['source_type']
            assert original_names[name]['label'] == copied_names[name]['label']

    def test_copy_independence_line_item_modification(self, simple_model):
        """Test that modifying line items in copy doesn't affect original."""
        copied: Model = simple_model.copy()
        
        # Modify a line item value in the copy
        copied._line_item_definitions[0].values[2023] = 999.0
        
        # Rebuild the copied model to reflect changes
        copied_rebuilt = Model(
            line_items=copied._line_item_definitions,
            years=copied.years,
            categories=copied._category_definitions
        )
        
        # Original should be unchanged
        assert simple_model.get_value("revenue", 2023) == 100.0
        assert copied_rebuilt.get_value("revenue", 2023) == 999.0

    def test_copy_independence_assumption_modification(self, simple_model):
        """Test that modifying assumption line_items in copy doesn't affect original."""
        copied: Model = simple_model.copy()
        
        # Find the growth_rate line item and modify its value in the copy
        growth_rate_item = next(item for item in copied._line_item_definitions if item.name == "growth_rate")
        growth_rate_item.values[2023] = 0.5
        
        # Rebuild the copied model to reflect changes
        copied_rebuilt = Model(
            line_items=copied._line_item_definitions,
            years=copied.years,
            categories=copied._category_definitions
        )
        
        # Original should be unchanged
        assert simple_model.get_value("growth_rate", 2023) == 0.1
        assert copied_rebuilt.get_value("growth_rate", 2023) == 0.5

    def test_copy_with_complex_model(self, complex_model):
        """Test copy() with a more complex model including formulas."""
        copied = complex_model.copy()
        
        # Verify it's a different object
        assert copied is not complex_model
        
        # Verify all years work
        for year in complex_model.years:
            assert copied.get_value("revenue", year) == complex_model.get_value("revenue", year)
            assert copied.get_value("expenses", year) == complex_model.get_value("expenses", year)
            assert copied.get_value("profit", year) == complex_model.get_value("profit", year)
            
            # Test category totals if they exist
            try:
                assert copied.get_value("total_income", year) == complex_model.get_value("total_income", year)
                assert copied.get_value("total_costs", year) == complex_model.get_value("total_costs", year)
            except KeyError:
                pass  # Category totals might not exist

    def test_copy_preserves_model_functionality(self, simple_model: Model):
        """Test that copied model maintains all Model functionality."""
        copied = simple_model.copy()
        
        # Test magic method access
        assert copied["revenue", 2023] == simple_model["revenue", 2023]
        assert copied["expenses", 2024] == simple_model["expenses", 2024]
        
        # Test helper methods
        assert copied.line_item("revenue").label == simple_model.line_item("revenue").label
        assert copied.line_item("revenue").value_format == simple_model.line_item("revenue").value_format

        # Test item info
        revenue_info_original = simple_model._get_item_metadata("revenue")
        revenue_info_copied = copied._get_item_metadata("revenue")
        assert revenue_info_original == revenue_info_copied

    def test_copy_with_empty_lists(self):
        """Test copy() with minimal model (auto-generated categories)."""
        line_items = [
            LineItem(name="item1", category="test", values={2023: 100.0})
        ]
        
        minimal_model = Model(
            line_items=line_items,
            years=[2023]
        )
        
        copied = minimal_model.copy()
        
        assert copied is not minimal_model
        assert copied.get_value("item1", 2023) == 100.0
        assert len(copied._category_definitions) == 1  # Auto-generated

    def test_copy_preserves_namespace_access(self, simple_model):
        """Test that copy preserves tables and charts namespace access."""
        copied = simple_model.copy()
        
        # Test that namespace properties work
        assert hasattr(copied, 'tables')
        assert hasattr(copied, 'charts')
        
        # Test that they return the expected types
        from pyproforma.tables import Tables
        from pyproforma.charts import Charts
        
        assert isinstance(copied.tables, Tables)
        assert isinstance(copied.charts, Charts)