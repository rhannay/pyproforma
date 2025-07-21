import pytest
from pyproforma.models.line_item_generator.abc_class import LineItemGenerator
from pyproforma.models.line_item_generator.debt import Debt
from pyproforma.models.line_item_generator.short_term_debt import ShortTermDebt


class TestLineItemGeneratorRoundTrip:
    """Test round-trip serialization/deserialization of line item generators."""
    
    def test_debt_round_trip_basic(self):
        """Test basic debt round-trip without existing debt service."""
        # Create original debt instance
        original_debt = Debt(
            name="test_debt",
            par_amount={2024: 1000000, 2025: 500000},
            interest_rate=0.05,
            term=10
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'debt'
        assert debt_dict['name'] == 'test_debt'
        assert debt_dict['par_amount'] == {2024: 1000000, 2025: 500000}
        assert debt_dict['interest_rate'] == 0.05
        assert debt_dict['term'] == 10
        assert debt_dict['existing_debt_service'] is None
        
        # Create new instance from dict using factory
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify it's the right type
        assert isinstance(recreated_debt, Debt)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._par_amount == original_debt._par_amount
        assert recreated_debt._interest_rate == original_debt._interest_rate
        assert recreated_debt._term == original_debt._term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
        
        # Verify values match for a sample year
        # We need to create interim_values_by_year for testing get_values
        interim_values_by_year = {
            2024: {},
            2025: {},
            2026: {}
        }
        test_year = 2025
        original_values = original_debt.get_values(interim_values_by_year, test_year)
        recreated_values = recreated_debt.get_values(interim_values_by_year, test_year)
        
        # Compare each key individually to handle float precision
        for key in original_values:
            assert abs(original_values[key] - recreated_values[key]) < 1e-10
    
    def test_debt_round_trip_with_existing_debt_service(self):
        """Test debt round-trip with existing debt service."""
        existing_debt_service = [
            {'year': 2024, 'principal': 50000, 'interest': 25000},
            {'year': 2025, 'principal': 52000, 'interest': 23000}
        ]
        
        # Create original debt instance
        original_debt = Debt(
            name="complex_debt",
            par_amount={2026: 2000000},
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
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._par_amount == original_debt._par_amount
        assert recreated_debt._interest_rate == original_debt._interest_rate
        assert recreated_debt._term == original_debt._term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service
        
        # Verify values match for years with existing debt service
        interim_values_by_year = {
            2024: {},
            2025: {},
            2026: {},
            2027: {}
        }
        for test_year in [2024, 2025, 2026]:
            original_values = original_debt.get_values(interim_values_by_year, test_year)
            recreated_values = recreated_debt.get_values(interim_values_by_year, test_year)
            
            # Compare each key individually to handle float precision
            for key in original_values:
                assert abs(original_values[key] - recreated_values[key]) < 1e-10
    
    def test_debt_round_trip_with_dynamic_parameters(self):
        """Test debt round-trip with dynamic parameters (strings)."""
        # Create original debt instance with string parameters
        original_debt = Debt(
            name="dynamic_debt",
            par_amount="debt_issuance",
            interest_rate="market_rate",
            term="debt_term"
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'debt'
        assert debt_dict['name'] == 'dynamic_debt'
        assert debt_dict['par_amount'] == "debt_issuance"
        assert debt_dict['interest_rate'] == "market_rate"
        assert debt_dict['term'] == "debt_term"
        
        # Create new instance from dict
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._par_amount == original_debt._par_amount
        assert recreated_debt._interest_rate == original_debt._interest_rate
        assert recreated_debt._term == original_debt._term
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
    
    def test_short_term_debt_round_trip_basic(self):
        """Test basic short-term debt round-trip."""
        # Create original short-term debt instance
        original_debt = ShortTermDebt(
            name="credit_line",
            draws={2024: 500000, 2025: 300000},
            paydown={2025: 200000, 2026: 600000},
            begin_balance=1000000,
            interest_rate=0.04
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
        
        # Create new instance from dict using factory
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify it's the right type
        assert isinstance(recreated_debt, ShortTermDebt)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
        
        # Verify values match for sample years
        interim_values_by_year = {
            2024: {},
            2025: {},
            2026: {}
        }
        for test_year in [2024, 2025, 2026]:
            original_values = original_debt.get_values(interim_values_by_year, test_year)
            recreated_values = recreated_debt.get_values(interim_values_by_year, test_year)
            
            # Compare each key individually to handle float precision
            for key in original_values:
                assert abs(original_values[key] - recreated_values[key]) < 1e-10
    
    def test_short_term_debt_round_trip_empty_draws_paydown(self):
        """Test short-term debt round-trip with empty draws and paydown."""
        # Create original short-term debt instance with minimal data
        original_debt = ShortTermDebt(
            name="simple_line",
            draws={},
            paydown={},
            begin_balance=750000,
            interest_rate=0.035
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['draws'] == {}
        assert debt_dict['paydown'] == {}
        
        # Create new instance from dict
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate
        
        # Verify values match
        interim_values_by_year = {2024: {}}
        test_year = 2024
        original_values = original_debt.get_values(interim_values_by_year, test_year)
        recreated_values = recreated_debt.get_values(interim_values_by_year, test_year)
        
        # Compare each key individually to handle float precision
        for key in original_values:
            assert abs(original_values[key] - recreated_values[key]) < 1e-10
    
    def test_short_term_debt_round_trip_with_dynamic_parameters(self):
        """Test short-term debt round-trip with dynamic parameters."""
        # Create original short-term debt instance with string parameters
        original_debt = ShortTermDebt(
            name="dynamic_line",
            draws="credit_draws",
            paydown="credit_payments",
            begin_balance=500000,
            interest_rate="variable_rate"
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['name'] == 'dynamic_line'
        assert debt_dict['draws'] == "credit_draws"
        assert debt_dict['paydown'] == "credit_payments"
        assert debt_dict['interest_rate'] == "variable_rate"
        
        # Create new instance from dict
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate
        
        # Verify defined names match
        assert recreated_debt.defined_names == original_debt.defined_names
    
    def test_short_term_debt_round_trip_with_interest_rate_dict(self):
        """Test short-term debt round-trip with year-specific interest rates."""
        # Create original short-term debt instance with interest rate dict
        original_debt = ShortTermDebt(
            name="variable_line",
            draws={2024: 100000},
            paydown={2025: 50000},
            begin_balance=500000,
            interest_rate={2024: 0.05, 2025: 0.06, 2026: 0.065}
        )
        
        # Convert to dict
        debt_dict = original_debt.to_dict()
        
        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['interest_rate'] == {2024: 0.05, 2025: 0.06, 2026: 0.065}
        
        # Create new instance from dict
        recreated_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate
        
        # Verify values match for sample years
        interim_values_by_year = {
            2024: {},
            2025: {},
            2026: {}
        }
        for test_year in [2024, 2025, 2026]:
            original_values = original_debt.get_values(interim_values_by_year, test_year)
            recreated_values = recreated_debt.get_values(interim_values_by_year, test_year)
            
            # Compare each key individually to handle float precision
            for key in original_values:
                assert abs(original_values[key] - recreated_values[key]) < 1e-10
    
    def test_multiple_round_trips(self):
        """Test that multiple round-trips don't introduce errors."""
        # Create original debt
        original_debt = Debt(
            name="multi_round_trip",
            par_amount={2024: 1500000},
            interest_rate=0.055,
            term=20
        )
        
        # Perform multiple round-trips
        current_debt = original_debt
        for i in range(5):
            debt_dict = current_debt.to_dict()
            current_debt = LineItemGenerator.from_dict(debt_dict)
        
        # Verify final result matches original
        assert current_debt.name == original_debt.name
        assert current_debt._par_amount == original_debt._par_amount
        assert current_debt._interest_rate == original_debt._interest_rate
        assert current_debt._term == original_debt._term
        
        # Verify values still match
        interim_values_by_year = {2024: {}, 2025: {}}
        test_year = 2025
        original_values = original_debt.get_values(interim_values_by_year, test_year)
        final_values = current_debt.get_values(interim_values_by_year, test_year)
        
        # Compare each key individually to handle float precision
        for key in original_values:
            assert abs(original_values[key] - final_values[key]) < 1e-10
    
    def test_registry_contains_both_types(self):
        """Test that both line item generator types are registered."""
        assert 'debt' in LineItemGenerator._registry
        assert 'short_term_debt' in LineItemGenerator._registry
        assert LineItemGenerator._registry['debt'] == Debt
        assert LineItemGenerator._registry['short_term_debt'] == ShortTermDebt
    
    def test_from_dict_invalid_type(self):
        """Test that from_dict raises error for invalid type."""
        with pytest.raises(ValueError, match="Unknown line item generator type: invalid_type"):
            LineItemGenerator.from_dict({'type': 'invalid_type'})
    
    def test_from_dict_missing_type(self):
        """Test that from_dict raises error for missing type."""
        with pytest.raises(ValueError, match="Configuration must include a 'type' field"):
            LineItemGenerator.from_dict({'name': 'test'})
    
    def test_cross_generator_round_trip(self):
        """Test creating different line item generator types from dicts."""
        # Create configs for both types
        debt_config = {
            'type': 'debt',
            'name': 'test_debt',
            'par_amount': {2024: 1000000},
            'interest_rate': 0.05,
            'term': 10
        }
        
        short_term_config = {
            'type': 'short_term_debt',
            'name': 'test_line',
            'draws': {2024: 100000},
            'paydown': {2025: 50000},
            'begin_balance': 500000,
            'interest_rate': 0.04
        }
        
        # Create instances using factory
        debt_instance = LineItemGenerator.from_dict(debt_config)
        short_term_instance = LineItemGenerator.from_dict(short_term_config)
        
        # Verify types
        assert isinstance(debt_instance, Debt)
        assert isinstance(short_term_instance, ShortTermDebt)
        
        # Verify round-trip works for both
        debt_round_trip = LineItemGenerator.from_dict(debt_instance.to_dict())
        short_term_round_trip = LineItemGenerator.from_dict(short_term_instance.to_dict())
        
        assert isinstance(debt_round_trip, Debt)
        assert isinstance(short_term_round_trip, ShortTermDebt)
        
        # Verify values match
        interim_values_by_year = {2024: {}, 2025: {}}
        
        debt_orig_values = debt_instance.get_values(interim_values_by_year, 2024)
        debt_round_values = debt_round_trip.get_values(interim_values_by_year, 2024)
        for key in debt_orig_values:
            assert abs(debt_orig_values[key] - debt_round_values[key]) < 1e-10
        
        short_term_orig_values = short_term_instance.get_values(interim_values_by_year, 2024)
        short_term_round_values = short_term_round_trip.get_values(interim_values_by_year, 2024)
        for key in short_term_orig_values:
            assert abs(short_term_orig_values[key] - short_term_round_values[key]) < 1e-10