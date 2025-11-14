"""Tests for generator field access pattern and GeneratorResults."""

import pytest

from pyproforma.models.generator.debt import Debt
from pyproforma.models.line_item import LineItem
from pyproforma.models.model.model import Model


class TestGeneratorFieldAccessPattern:
    """Test the new generator field access pattern with 'generator_name: field_name' syntax."""

    def test_generator_field_formula(self):
        """Test accessing generator fields via formula syntax."""
        # Create a simple model with debt generator
        years = [2020, 2021]
        
        debt = Debt(
            name="my_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        # Create line items that access generator fields
        interest_line = LineItem(
            name="interest_expense",
            formula="my_debt: interest",
        )
        
        principal_line = LineItem(
            name="principal_payment",
            formula="my_debt: principal",
        )
        
        model = Model(
            line_items=[interest_line, principal_line],
            years=years,
            generators=[debt],
        )
        
        # Verify we can access the line items that use generator fields
        assert model.value("interest_expense", 2020) > 0
        assert model.value("principal_payment", 2020) > 0
        
    def test_generator_field_not_accessible_as_line_item(self):
        """Test that generator fields are not automatically accessible as line items."""
        years = [2020, 2021]
        
        debt = Debt(
            name="my_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        # Trying to access the generator field directly should raise an error
        with pytest.raises(KeyError):
            model.value("my_debt_interest", 2020)
        
        with pytest.raises(KeyError):
            model.value("interest", 2020)
            
        # But the full dotted name should work
        assert model.value("my_debt.interest", 2020) > 0


class TestGeneratorResults:
    """Test the GeneratorResults class for accessing generator field values."""
    
    def test_generator_results_basic(self):
        """Test basic GeneratorResults functionality."""
        years = [2020, 2021, 2022]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        # Get generator results
        gen_results = model.generator("test_debt")
        
        # Verify properties
        assert gen_results.name == "test_debt"
        assert set(gen_results.field_names) == {
            "principal",
            "interest",
            "bond_proceeds",
            "debt_outstanding",
        }
        
    def test_generator_results_field_access(self):
        """Test accessing individual fields via GeneratorResults."""
        years = [2020, 2021]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        gen_results = model.generator("test_debt")
        
        # Test getting all years for a field
        interest_values = gen_results.field("interest")
        assert isinstance(interest_values, dict)
        assert 2020 in interest_values
        assert 2021 in interest_values
        assert interest_values[2020] > 0
        
        # Test getting specific year for a field
        interest_2020 = gen_results.field("interest", 2020)
        assert isinstance(interest_2020, (int, float))
        assert interest_2020 > 0
        assert interest_2020 == interest_values[2020]
        
    def test_generator_results_invalid_field(self):
        """Test error handling for invalid field names."""
        years = [2020, 2021]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        gen_results = model.generator("test_debt")
        
        # Accessing non-existent field should raise error
        with pytest.raises(KeyError):
            gen_results.field("nonexistent_field")
            
    def test_generator_results_to_dataframe(self):
        """Test converting generator results to DataFrame."""
        years = [2020, 2021]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        gen_results = model.generator("test_debt")
        df = gen_results.to_dataframe()
        
        # Verify DataFrame structure
        assert list(df.columns) == years
        assert set(df.index) == set(gen_results.field_names)
        
        # Verify values
        assert df.loc["interest", 2020] > 0
        assert df.loc["principal", 2020] > 0

    def test_generator_results_subscriptable(self):
        """Test that GeneratorResults supports bracket notation."""
        years = [2020, 2021]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        gen_results = model.generator("test_debt")
        
        # Test subscriptable access
        principal_values = gen_results['principal']
        assert isinstance(principal_values, dict)
        assert 2020 in principal_values
        assert 2021 in principal_values
        
        # Test that it returns the same result as .field()
        assert gen_results['principal'] == gen_results.field('principal')
        assert gen_results['interest'] == gen_results.field('interest')
        
        # Test with all fields
        for field in gen_results.field_names:
            assert gen_results[field] == gen_results.field(field)

    def test_generator_results_subscriptable_invalid_field(self):
        """Test that subscriptable access raises error for invalid field."""
        years = [2020, 2021]
        
        debt = Debt(
            name="test_debt",
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30,
        )
        
        model = Model(
            line_items=[],
            years=years,
            generators=[debt],
        )
        
        gen_results = model.generator("test_debt")
        
        # Accessing non-existent field with bracket notation should raise error
        with pytest.raises(KeyError):
            gen_results['nonexistent_field']
