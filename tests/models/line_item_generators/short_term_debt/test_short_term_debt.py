from pyproforma.models.line_item_generator.short_term_debt import ShortTermDebt
from .utils import _is_close, _calculate_interest, _calculate_debt_outstanding
import pytest


class TestShortTermDebtBasic:
    """Test basic functionality of ShortTermDebt LineItemGenerator."""
    
    def test_defined_names(self):
        """Test that defined_names returns the correct line item names."""
        debt = ShortTermDebt(
            name='test_debt',
            draws={2020: 100000},
            paydown={2021: 50000},
            begin_balance=500000,
            interest_rate=0.05
        )
        
        expected_names = [
            'test_debt.debt_outstanding',
            'test_debt.draw',
            'test_debt.principal',
            'test_debt.interest'
        ]
        
        assert debt.defined_names == expected_names

    def test_name_validation(self):
        """Test that invalid names raise ValueError."""
        with pytest.raises(ValueError, match="Short term debt name must only contain"):
            ShortTermDebt(
                name='invalid name with spaces',
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=0.05
            )

    def test_negative_interest_rate_validation(self):
        """Test that negative interest rates raise ValueError."""
        with pytest.raises(ValueError, match="Interest rate cannot be negative"):
            ShortTermDebt(
                name='test_debt',
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate=-0.01
            )

    def test_negative_interest_rate_dict_validation(self):
        """Test that negative interest rates in dict raise ValueError."""
        with pytest.raises(ValueError, match="Interest rate for year .* cannot be negative"):
            ShortTermDebt(
                name='test_debt',
                draws={},
                paydown={},
                begin_balance=0,
                interest_rate={2020: 0.05, 2021: -0.01}
            )

    def test_negative_draw_validation(self):
        """Test that negative draw amounts raise ValueError."""
        with pytest.raises(ValueError, match="Draw amount for year .* cannot be negative"):
            ShortTermDebt(
                name='test_debt',
                draws={2020: -100000},
                paydown={},
                begin_balance=0,
                interest_rate=0.05
            )

    def test_negative_paydown_validation(self):
        """Test that negative paydown amounts raise ValueError."""
        with pytest.raises(ValueError, match="Paydown amount for year .* cannot be negative"):
            ShortTermDebt(
                name='test_debt',
                draws={},
                paydown={2020: -50000},
                begin_balance=0,
                interest_rate=0.05
            )


class TestShortTermDebtFixedParameters:
    """Test ShortTermDebt with fixed parameter values."""
    
    def test_simple_debt_no_activity(self):
        """Test debt with begin balance but no draws or paydowns."""
        debt = ShortTermDebt(
            name='simple_debt',
            draws={},
            paydown={},
            begin_balance=1000000,
            interest_rate=0.05
        )
        
        interim_values = {2019: {}, 2020: {}, 2021: {}}
        
        # Test year 2020
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['simple_debt.debt_outstanding'] == 1000000
        assert values_2020['simple_debt.draw'] == 0.0
        assert values_2020['simple_debt.principal'] == 0.0
        assert values_2020['simple_debt.interest'] == 50000  # 1M * 0.05
        
        # Test year 2021 (no activity, same balance)
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['simple_debt.debt_outstanding'] == 1000000
        assert values_2021['simple_debt.draw'] == 0.0
        assert values_2021['simple_debt.principal'] == 0.0
        assert values_2021['simple_debt.interest'] == 50000  # 1M * 0.05

    def test_debt_with_draws_only(self):
        """Test debt with draws but no paydowns."""
        debt = ShortTermDebt(
            name='growth_debt',
            draws={2020: 200000, 2021: 300000},
            paydown={},
            begin_balance=500000,
            interest_rate=0.06
        )
        
        interim_values = {2019: {}, 2020: {}, 2021: {}, 2022: {}}
        
        # Test year 2020 (first draw)
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['growth_debt.debt_outstanding'] == 700000  # 500k + 200k
        assert values_2020['growth_debt.draw'] == 200000
        assert values_2020['growth_debt.principal'] == 0.0
        assert _is_close(values_2020['growth_debt.interest'], 30000)  # 500k * 0.06
        
        # Test year 2021 (second draw)
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['growth_debt.debt_outstanding'] == 1000000  # 700k + 300k
        assert values_2021['growth_debt.draw'] == 300000
        assert values_2021['growth_debt.principal'] == 0.0
        assert _is_close(values_2021['growth_debt.interest'], 42000)  # 700k * 0.06

    def test_debt_with_paydowns_only(self):
        """Test debt with paydowns but no draws."""
        debt = ShortTermDebt(
            name='paydown_debt',
            draws={},
            paydown={2020: 100000, 2021: 150000},
            begin_balance=1000000,
            interest_rate=0.04
        )
        
        interim_values = {2019: {}, 2020: {}, 2021: {}, 2022: {}}
        
        # Test year 2020 (first paydown)
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['paydown_debt.debt_outstanding'] == 900000  # 1M - 100k
        assert values_2020['paydown_debt.draw'] == 0.0
        assert values_2020['paydown_debt.principal'] == 100000
        assert _is_close(values_2020['paydown_debt.interest'], 40000)  # 1M * 0.04
        
        # Test year 2021 (second paydown)
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['paydown_debt.debt_outstanding'] == 750000  # 900k - 150k
        assert values_2021['paydown_debt.draw'] == 0.0
        assert values_2021['paydown_debt.principal'] == 150000
        assert _is_close(values_2021['paydown_debt.interest'], 36000)  # 900k * 0.04

    def test_debt_with_draws_and_paydowns(self):
        """Test debt with both draws and paydowns."""
        debt = ShortTermDebt(
            name='mixed_debt',
            draws={2020: 500000, 2021: 300000},
            paydown={2021: 200000, 2022: 600000},
            begin_balance=1000000,
            interest_rate=0.05
        )
        
        interim_values = {2019: {}, 2020: {}, 2021: {}, 2022: {}}
        
        # Test year 2020 (draw only)
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['mixed_debt.debt_outstanding'] == 1500000  # 1M + 500k
        assert values_2020['mixed_debt.draw'] == 500000
        assert values_2020['mixed_debt.principal'] == 0.0
        assert _is_close(values_2020['mixed_debt.interest'], 50000)  # 1M * 0.05
        
        # Test year 2021 (draw and paydown)
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['mixed_debt.debt_outstanding'] == 1600000  # 1.5M + 300k - 200k
        assert values_2021['mixed_debt.draw'] == 300000
        assert values_2021['mixed_debt.principal'] == 200000
        assert _is_close(values_2021['mixed_debt.interest'], 75000)  # 1.5M * 0.05
        
        # Test year 2022 (paydown only)
        values_2022 = debt.get_values(interim_values, 2022)
        assert values_2022['mixed_debt.debt_outstanding'] == 1000000  # 1.6M - 600k
        assert values_2022['mixed_debt.draw'] == 0.0
        assert values_2022['mixed_debt.principal'] == 600000
        assert _is_close(values_2022['mixed_debt.interest'], 80000)  # 1.6M * 0.05

    def test_year_before_start_year(self):
        """Test validation that draws and paydowns cannot be prior to start year."""
        # Test that draws prior to start year raise error
        debt1 = ShortTermDebt(
            name='early_draws_debt',
            draws={2018: 500000},  # Before start year (2020)
            paydown={},
            begin_balance=0,
            interest_rate=0.05
        )
        
        interim_values = {2020: {}, 2021: {}, 2022: {}, 2023: {}}
        
        with pytest.raises(ValueError, match="Draw year .* is prior to start year"):
            debt1.get_values(interim_values, 2020)
        
        # Test that paydowns prior to start year raise error
        debt2 = ShortTermDebt(
            name='early_paydown_debt',
            draws={},
            paydown={2019: 100000},  # Before start year (2020)
            begin_balance=500000,
            interest_rate=0.05
        )
        
        with pytest.raises(ValueError, match="Paydown year .* is prior to start year"):
            debt2.get_values(interim_values, 2020)
        
        # Test that draws/paydowns at or after start year work correctly
        debt3 = ShortTermDebt(
            name='valid_debt',
            draws={2020: 300000, 2022: 500000},  # At and after start year
            paydown={2021: 100000},  # After start year
            begin_balance=1000000,
            interest_rate=0.05
        )
        
        # This should work without errors
        values_2020 = debt3.get_values(interim_values, 2020)
        assert values_2020['valid_debt.debt_outstanding'] == 1300000  # 1000k + 300k
        assert values_2020['valid_debt.draw'] == 300000
        assert values_2020['valid_debt.principal'] == 0.0


class TestShortTermDebtDynamicParameters:
    """Test ShortTermDebt with dynamic parameter lookups from interim_values_by_year."""
    
    def test_dynamic_interest_rate(self):
        """Test debt with interest rate looked up from interim_values_by_year."""
        debt = ShortTermDebt(
            name='variable_debt',
            draws={},
            paydown={},
            begin_balance=1000000,
            interest_rate='prime_rate',  # String to lookup
        )
        
        interim_values = {
            # 2019: {},
            2020: {'prime_rate': 0.03},
            2021: {'prime_rate': 0.045}
        }
        
        # Test year 2020 with 3% rate
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['variable_debt.debt_outstanding'] == 1000000
        assert _is_close(values_2020['variable_debt.interest'], 30000)  # 1M * 0.03
        
        # Test year 2021 with 4.5% rate
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['variable_debt.debt_outstanding'] == 1000000
        assert _is_close(values_2021['variable_debt.interest'], 45000)  # 1M * 0.045

    def test_fixed_begin_balance(self):
        """Test debt with fixed begin balance."""
        debt = ShortTermDebt(
            name='fixed_debt',
            draws={},
            paydown={},
            begin_balance=750000,  # Fixed value
            interest_rate=0.05
        )
        
        interim_values = {
            2020: {},
            2021: {}
        }
        
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['fixed_debt.debt_outstanding'] == 750000
        assert _is_close(values_2020['fixed_debt.interest'], 37500)  # 750k * 0.05

    def test_dynamic_draws_and_paydown(self):
        """Test debt with draws and paydown looked up from interim_values_by_year."""
        debt = ShortTermDebt(
            name='flex_debt',
            draws='annual_draws',  # String to lookup
            paydown='annual_paydown',  # String to lookup
            begin_balance=500000,
            interest_rate=0.04
        )
        
        interim_values = {
            2019: {'annual_draws': 0, 'annual_paydown': 0},
            2020: {'annual_draws': 200000, 'annual_paydown': 0},
            2021: {'annual_draws': 100000, 'annual_paydown': 150000}
        }
        
        # Test year 2020
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['flex_debt.debt_outstanding'] == 700000  # 500k + 200k
        assert values_2020['flex_debt.draw'] == 200000
        assert values_2020['flex_debt.principal'] == 0.0
        assert _is_close(values_2020['flex_debt.interest'], 20000)  # 500k * 0.04
        
        # Test year 2021
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['flex_debt.debt_outstanding'] == 650000  # 700k + 100k - 150k
        assert values_2021['flex_debt.draw'] == 100000
        assert values_2021['flex_debt.principal'] == 150000
        assert _is_close(values_2021['flex_debt.interest'], 28000)  # 700k * 0.04

    def test_interest_rate_dict(self):
        """Test debt with year-specific interest rates provided as dict."""
        debt = ShortTermDebt(
            name='variable_rate_debt',
            draws={2020: 100000, 2021: 50000},
            paydown={2021: 30000, 2022: 120000},
            begin_balance=500000,
            interest_rate={2020: 0.04, 2021: 0.05, 2022: 0.06}  # Year-specific rates
        )
        
        interim_values = {
            2020: {},
            2021: {},
            2022: {}
        }
        
        # Test year 2020 - should use 4% rate
        values_2020 = debt.get_values(interim_values, 2020)
        assert values_2020['variable_rate_debt.debt_outstanding'] == 600000  # 500k + 100k
        assert values_2020['variable_rate_debt.draw'] == 100000
        assert values_2020['variable_rate_debt.principal'] == 0.0
        assert _is_close(values_2020['variable_rate_debt.interest'], 20000)  # 500k * 0.04
        
        # Test year 2021 - should use 5% rate
        values_2021 = debt.get_values(interim_values, 2021)
        assert values_2021['variable_rate_debt.debt_outstanding'] == 620000  # 600k + 50k - 30k
        assert values_2021['variable_rate_debt.draw'] == 50000
        assert values_2021['variable_rate_debt.principal'] == 30000
        assert _is_close(values_2021['variable_rate_debt.interest'], 30000)  # 600k * 0.05
        
        # Test year 2022 - should use 6% rate
        values_2022 = debt.get_values(interim_values, 2022)
        assert values_2022['variable_rate_debt.debt_outstanding'] == 500000  # 620k + 0 - 120k
        assert values_2022['variable_rate_debt.draw'] == 0.0
        assert values_2022['variable_rate_debt.principal'] == 120000
        assert _is_close(values_2022['variable_rate_debt.interest'], 37200)  # 620k * 0.06

    def test_interest_rate_dict_missing_year_error(self):
        """Test that missing year in interest rate dict raises proper error."""
        debt = ShortTermDebt(
            name='incomplete_rate_debt',
            draws={2020: 100000},
            paydown={},
            begin_balance=500000,
            interest_rate={2020: 0.04, 2022: 0.06}  # Missing 2021
        )
        
        interim_values = {
            2020: {},
            2021: {},
            2022: {}
        }
        
        # Test year 2020 - should work
        values_2020 = debt.get_values(interim_values, 2020)
        assert _is_close(values_2020['incomplete_rate_debt.interest'], 20000)  # 500k * 0.04
        
        # Test year 2021 - should raise error for missing interest rate
        with pytest.raises(ValueError, match="Interest rate for year 2021 not found in interest rate dictionary"):
            debt.get_values(interim_values, 2021)

    def test_missing_dynamic_parameter_error(self):
        """Test that missing dynamic parameters raise appropriate errors."""
        debt = ShortTermDebt(
            name='error_debt',
            draws={},
            paydown={},
            begin_balance=1000000,
            interest_rate='missing_rate'
        )
        
        interim_values = {2020: {}}  # missing_rate not provided
        
        with pytest.raises(ValueError, match="Could not find interest rate 'missing_rate'"):
            debt.get_values(interim_values, 2020)

    def test_none_dynamic_parameter_error(self):
        """Test that None values in dynamic parameters raise appropriate errors."""
        debt = ShortTermDebt(
            name='none_debt',
            draws={},
            paydown={},
            begin_balance=1000000,
            interest_rate='none_rate'
        )
        
        interim_values = {2020: {'none_rate': None}}
        
        with pytest.raises(ValueError, match="Interest rate 'none_rate' for year .* is None"):
            debt.get_values(interim_values, 2020)


class TestShortTermDebtDefaults:
    """Test ShortTermDebt with default parameter values."""
    
    def test_default_parameters(self):
        """Test debt with minimal parameters using defaults."""
        debt = ShortTermDebt(name='minimal_debt')
        
        interim_values = {2024: {}}
        
        values = debt.get_values(interim_values, 2024)
        assert values['minimal_debt.debt_outstanding'] == 0.0
        assert values['minimal_debt.draw'] == 0.0
        assert values['minimal_debt.principal'] == 0.0
        assert values['minimal_debt.interest'] == 0.0

    def test_none_draws_and_paydown(self):
        """Test debt with explicit None for draws and paydown."""
        debt = ShortTermDebt(
            name='none_debt',
            draws=None,
            paydown=None,
            begin_balance=100000,
            interest_rate=0.05
        )
        
        interim_values = {2019: {}, 2020: {}}
        
        values = debt.get_values(interim_values, 2020)
        assert values['none_debt.debt_outstanding'] == 100000
        assert values['none_debt.draw'] == 0.0
        assert values['none_debt.principal'] == 0.0
        assert _is_close(values['none_debt.interest'], 5000)  # 100k * 0.05