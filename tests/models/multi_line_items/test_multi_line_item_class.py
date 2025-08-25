import pytest

from pyproforma.models.multi_line_item.abc_class import MultiLineItem
from pyproforma.models.multi_line_item.debt import Debt
from pyproforma.models.multi_line_item.short_term_debt import ShortTermDebt


class TestMultiLineItemRoundTrip:
    """Test round-trip serialization/deserialization of multi line items."""

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
        recreated_debt = MultiLineItem.from_dict(debt_dict)

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
        recreated_debt = MultiLineItem.from_dict(debt_dict)

        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._par_amount == original_debt._par_amount
        assert recreated_debt._interest_rate == original_debt._interest_rate
        assert recreated_debt._term == original_debt._term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service

    def test_debt_round_trip_with_string_parameters(self):
        """Test debt round-trip with string parameters for dynamic lookup."""
        # Create original debt instance with string parameters
        original_debt = Debt(
            name="dynamic_debt",
            par_amount="bond_proceeds",  # string parameter
            interest_rate="market_rate",  # string parameter
            term="loan_term"  # string parameter
        )

        # Convert to dict
        debt_dict = original_debt.to_dict()

        # Verify dict structure
        assert debt_dict['type'] == 'debt'
        assert debt_dict['par_amount'] == "bond_proceeds"
        assert debt_dict['interest_rate'] == "market_rate"
        assert debt_dict['term'] == "loan_term"

        # Create new instance from dict
        recreated_debt = MultiLineItem.from_dict(debt_dict)

        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._par_amount == original_debt._par_amount
        assert recreated_debt._interest_rate == original_debt._interest_rate
        assert recreated_debt._term == original_debt._term
        assert recreated_debt.existing_debt_service == original_debt.existing_debt_service

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
        recreated_debt = MultiLineItem.from_dict(debt_dict)

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
        recreated_debt = MultiLineItem.from_dict(debt_dict)

        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate

    def test_short_term_debt_round_trip_with_dict_interest_rate(self):
        """Test short-term debt round-trip with year-specific interest rates."""
        # Create original short-term debt instance with year-specific rates
        original_debt = ShortTermDebt(
            name="variable_line",
            draws={2024: 500000},
            paydown={2025: 200000},
            begin_balance=1000000,
            interest_rate={2024: 0.05, 2025: 0.06, 2026: 0.065}  # dict interest rate
        )

        # Convert to dict
        debt_dict = original_debt.to_dict()

        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['interest_rate'] == {2024: 0.05, 2025: 0.06, 2026: 0.065}

        # Create new instance from dict
        recreated_debt = MultiLineItem.from_dict(debt_dict)

        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate

    def test_short_term_debt_round_trip_with_string_parameters(self):
        """Test short-term debt round-trip with string parameters for dynamic lookup."""
        # Create original short-term debt instance with string parameters
        original_debt = ShortTermDebt(
            name="dynamic_line",
            draws="capital_draws",  # string parameter
            paydown="principal_payments",  # string parameter
            begin_balance=500000,
            interest_rate="prime_rate"  # string parameter
        )

        # Convert to dict
        debt_dict = original_debt.to_dict()

        # Verify dict structure
        assert debt_dict['type'] == 'short_term_debt'
        assert debt_dict['draws'] == "capital_draws"
        assert debt_dict['paydown'] == "principal_payments"
        assert debt_dict['interest_rate'] == "prime_rate"

        # Create new instance from dict
        recreated_debt = MultiLineItem.from_dict(debt_dict)

        # Verify all attributes match
        assert recreated_debt.name == original_debt.name
        assert recreated_debt._draws == original_debt._draws
        assert recreated_debt._paydown == original_debt._paydown
        assert recreated_debt._begin_balance == original_debt._begin_balance
        assert recreated_debt._interest_rate == original_debt._interest_rate

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
            current_debt = MultiLineItem.from_dict(debt_dict)

        # Verify final result matches original
        assert current_debt.name == original_debt.name
        assert current_debt._par_amount == original_debt._par_amount
        assert current_debt._interest_rate == original_debt._interest_rate
        assert current_debt._term == original_debt._term

    def test_registry_contains_both_types(self):
        """Test that both multi line item types are registered."""
        assert 'debt' in MultiLineItem._registry
        assert 'short_term_debt' in MultiLineItem._registry
        assert MultiLineItem._registry['debt'] == Debt
        assert MultiLineItem._registry['short_term_debt'] == ShortTermDebt

    def test_from_dict_invalid_type(self):
        """Test that from_dict raises error for invalid type."""
        with pytest.raises(ValueError, match="Unknown multi line item type: invalid_type"):
            MultiLineItem.from_dict({'type': 'invalid_type'})

    def test_from_dict_missing_type(self):
        """Test that from_dict raises error for missing type."""
        with pytest.raises(ValueError, match="Configuration must include a 'type' field"):
            MultiLineItem.from_dict({'name': 'test'})

    def test_cross_generator_round_trip(self):
        """Test creating different multi line item types from dicts."""
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
        debt_instance = MultiLineItem.from_dict(debt_config)
        short_term_instance = MultiLineItem.from_dict(short_term_config)

        # Verify types
        assert isinstance(debt_instance, Debt)
        assert isinstance(short_term_instance, ShortTermDebt)

        # Verify round-trip works for both
        debt_round_trip = MultiLineItem.from_dict(debt_instance.to_dict())
        short_term_round_trip = MultiLineItem.from_dict(short_term_instance.to_dict())

        assert isinstance(debt_round_trip, Debt)
        assert isinstance(short_term_round_trip, ShortTermDebt)

        # Verify attributes match after round-trip
        assert debt_instance.name == debt_round_trip.name
        assert debt_instance._par_amount == debt_round_trip._par_amount
        assert debt_instance._interest_rate == debt_round_trip._interest_rate
        assert debt_instance._term == debt_round_trip._term

        assert short_term_instance.name == short_term_round_trip.name
        assert short_term_instance._draws == short_term_round_trip._draws
        assert short_term_instance._paydown == short_term_round_trip._paydown
        assert short_term_instance._begin_balance == short_term_round_trip._begin_balance
        assert short_term_instance._interest_rate == short_term_round_trip._interest_rate

    def test_json_compatibility(self):
        """Test that serialization works with JSON (string keys)."""
        # Create debt with integer keys
        original_debt = Debt(
            name="json_test",
            par_amount={2024: 1000000, 2025: 500000},
            interest_rate=0.05,
            term=10
        )

        # Simulate JSON round-trip (keys become strings)
        debt_dict = original_debt.to_dict()

        # Convert integer keys to strings (what happens in JSON)
        json_like_dict = debt_dict.copy()
        json_like_dict['par_amount'] = {str(k): v for k, v in debt_dict['par_amount'].items()}

        # Should still work with from_dict
        recreated_debt = MultiLineItem.from_dict(json_like_dict)

        # par_amount should be converted back to integer keys
        assert recreated_debt._par_amount == {2024: 1000000, 2025: 500000}

        # Test same for short term debt with dict interest rate
        original_short_term = ShortTermDebt(
            name="json_short_term",
            draws={2024: 100000, 2025: 150000},
            paydown={2026: 50000},
            begin_balance=500000,
            interest_rate={2024: 0.04, 2025: 0.045}
        )

        short_term_dict = original_short_term.to_dict()

        # Convert integer keys to strings
        json_like_short_term = short_term_dict.copy()
        json_like_short_term['draws'] = {str(k): v for k, v in short_term_dict['draws'].items()}
        json_like_short_term['paydown'] = {str(k): v for k, v in short_term_dict['paydown'].items()}
        json_like_short_term['interest_rate'] = {str(k): v for k, v in short_term_dict['interest_rate'].items()}

        # Should still work with from_dict
        recreated_short_term = MultiLineItem.from_dict(json_like_short_term)

        # Keys should be converted back to integers
        assert recreated_short_term._draws == {2024: 100000, 2025: 150000}
        assert recreated_short_term._paydown == {2026: 50000}
        assert recreated_short_term._interest_rate == {2024: 0.04, 2025: 0.045}
