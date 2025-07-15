import pytest
from pyproforma.generators.generator_class import Generator
from pyproforma.generators.debt import Debt
from pyproforma.generators.short_term_debt import ShortTermDebt


class TestGeneratorRoundTrip:
    """Test round-trip serialization/deserialization of generators."""
    
    def test_debt_round_trip_basic(self):
        """Test basic debt round-trip without existing debt service."""
        # Create original debt instance
        original_debt = Debt(
            name="test_debt",
            par_amounts={2024: 1000000, 2025: 500000},
            interest_rate=0.05,
            term=10
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'debt'
        assert debt_dict['name'] == 'test_debt'
        assert debt_dict['par_amounts'] == {2024: 1000000, 2025: 500000}
        assert debt_dict['interest_rate'] == 0.05
        assert debt_dict['term'] == 10
        assert debt_dict['existing_debt_service'] is None
        
        # Create new instance from dict using factory
        recreated_debt = Generator.from_dict(debt_dict)
        
        # Verify it's the right type
        assert isinstance(recreated_debt, Debt)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt.par_amounts == original_debt.par_amounts
        assert recreated_debt.interest_rate == original_debt.interest_rate
        assert recreated_debt.term == original_debt.term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
        
        # Verify values match for a sample year
        test_year = 2025
        original_values = original_debt.get_values(test_year)
        recreated_values = recreated_debt.get_values(test_year)
        assert original_values == recreated_values
    
    def test_debt_round_trip_with_existing_debt_service(self):
        """Test debt round-trip with existing debt service."""
        existing_debt_service = [
            {'year': 2024, 'principal': 50000, 'interest': 25000},
            {'year': 2025, 'principal': 52000, 'interest': 23000}
        ]
        
        # Create original debt instance
        original_debt = Debt(
            name="complex_debt",
            par_amounts={2026: 2000000},
            interest_rate=0.06,
            term=15,
            existing_debt_service=existing_debt_service
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure includes existing debt service
        assert debt_dict['type'] == 'debt'
        assert debt_dict['existing_debt_service'] == existing_debt_service
        
        # Create new instance from dict
        recreated_debt = Generator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt.par_amounts == original_debt.par_amounts
        assert recreated_debt.interest_rate == original_debt.interest_rate
        assert recreated_debt.term == original_debt.term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service
        
        # Verify values match for years with existing debt service
        for test_year in [2024, 2025, 2026]:
            original_values = original_debt.get_values(test_year)
            recreated_values = recreated_debt.get_values(test_year)
            assert original_values == recreated_values
    
    def test_short_term_debt_round_trip_basic(self):
        """Test basic short-term debt round-trip."""
        # Create original short-term debt instance
        original_debt = ShortTermDebt(
            name="credit_line",
            draws={2024: 500000, 2025: 300000},
            paydown={2025: 200000, 2026: 600000},
            begin_balance=1000000,
            interest_rate=0.04,
            start_year=2024
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['name'] == 'credit_line'
        assert debt_dict['draws'] == {2024: 500000, 2025: 300000}
        assert debt_dict['paydown'] == {2025: 200000, 2026: 600000}
        assert debt_dict['begin_balance'] == 1000000
        assert debt_dict['interest_rate'] == 0.04
        assert debt_dict['start_year'] == 2024
        
        # Create new instance from dict using factory
        recreated_debt = Generator.from_dict(debt_dict)
        
        # Verify it's the right type
        assert isinstance(recreated_debt, ShortTermDebt)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt.draws == original_debt.draws
        assert recreated_debt.paydown == original_debt.paydown
        assert recreated_debt.begin_balance == original_debt.begin_balance
        assert recreated_debt.interest_rate == original_debt.interest_rate
        assert recreated_debt.start_year == original_debt.start_year
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
        
        # Verify values match for sample years
        for test_year in [2024, 2025, 2026]:
            original_values = original_debt.get_values(test_year)
            recreated_values = recreated_debt.get_values(test_year)
            assert original_values == recreated_values
    
    def test_short_term_debt_round_trip_empty_draws_paydown(self):
        """Test short-term debt round-trip with empty draws and paydown."""
        # Create original short-term debt instance with minimal data
        original_debt = ShortTermDebt(
            name="simple_line",
            draws={},
            paydown={},
            begin_balance=750000,
            interest_rate=0.035,
            start_year=2023
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['draws'] == {}
        assert debt_dict['paydown'] == {}
        
        # Create new instance from dict
        recreated_debt = Generator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt.draws == original_debt.draws
        assert recreated_debt.paydown == original_debt.paydown
        assert recreated_debt.begin_balance == original_debt.begin_balance
        assert recreated_debt.interest_rate == original_debt.interest_rate
        assert recreated_debt.start_year == original_debt.start_year
        
        # Verify values match
        test_year = 2024
        original_values = original_debt.get_values(test_year)
        recreated_values = recreated_debt.get_values(test_year)
        assert original_values == recreated_values
    
    def test_multiple_round_trips(self):
        """Test that multiple round-trips don't introduce errors."""
        # Create original debt
        original_debt = Debt(
            name="multi_round_trip",
            par_amounts={2024: 1500000},
            interest_rate=0.055,
            term=20
        )
        
        # Perform multiple round-trips
        current_debt = original_debt
        for i in range(5):
            debt_dict = current_debt.to_dict()
            current_debt = Generator.from_dict(debt_dict)
        
        # Verify final result matches original
        assert current_debt.name == original_debt.name
        assert current_debt.par_amounts == original_debt.par_amounts
        assert current_debt.interest_rate == original_debt.interest_rate
        assert current_debt.term == original_debt.term
        
        # Verify values still match
        test_year = 2025
        original_values = original_debt.get_values(test_year)
        final_values = current_debt.get_values(test_year)
        assert original_values == final_values
    
    def test_registry_contains_both_types(self):
        """Test that both generator types are registered."""
        assert 'debt' in Generator._registry
        assert 'short_term_debt' in Generator._registry
        assert Generator._registry['debt'] == Debt
        assert Generator._registry['short_term_debt'] == ShortTermDebt
    
    def test_from_dict_invalid_type(self):
        """Test that from_dict raises error for invalid type."""
        with pytest.raises(ValueError, match="Unknown generator type: invalid_type"):
            Generator.from_dict({'type': 'invalid_type'})
    
    def test_from_dict_missing_type(self):
        """Test that from_dict raises error for missing type."""
        with pytest.raises(ValueError, match="Configuration must include a 'type' field"):
            Generator.from_dict({'name': 'test'})
    
    def test_cross_generator_round_trip(self):
        """Test creating different generator types from dicts."""
        # Create configs for both types
        debt_config = {
            'type': 'debt',
            'name': 'test_debt',
            'par_amounts': {2024: 1000000},
            'interest_rate': 0.05,
            'term': 10
        }
        
        short_term_config = {
            'type': 'short_term_debt',
            'name': 'test_line',
            'draws': {2024: 100000},
            'paydown': {2025: 50000},
            'begin_balance': 500000,
            'interest_rate': 0.04,
            'start_year': 2024
        }
        
        # Create instances using factory
        debt_instance = Generator.from_dict(debt_config)
        short_term_instance = Generator.from_dict(short_term_config)
        
        # Verify types
        assert isinstance(debt_instance, Debt)
        assert isinstance(short_term_instance, ShortTermDebt)
        
        # Verify round-trip works for both
        debt_round_trip = Generator.from_dict(debt_instance.to_dict())
        short_term_round_trip = Generator.from_dict(short_term_instance.to_dict())
        
        assert isinstance(debt_round_trip, Debt)
        assert isinstance(short_term_round_trip, ShortTermDebt)
        
        # Verify values match
        assert debt_instance.get_values(2024) == debt_round_trip.get_values(2024)
        assert short_term_instance.get_values(2024) == short_term_round_trip.get_values(2024)
