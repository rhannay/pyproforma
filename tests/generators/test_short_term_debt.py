import pytest
from pyproforma.generators.short_term_debt import ShortTermDebt


class TestShortTermDebt:
    def test_init_basic(self):
        """Test basic initialization of ShortTermDebt"""
        draws = {2020: 100000, 2021: 50000}
        paydown = {2021: 25000, 2022: 75000}
        begin_balance = 200000
        interest_rate = 0.05
        start_year = 2020
        
        debt = ShortTermDebt('revolving_credit', draws, paydown, begin_balance, interest_rate, start_year)
        
        assert debt.name == 'revolving_credit'
        assert debt.draws == draws
        assert debt.paydown == paydown
        assert debt.begin_balance == begin_balance
        assert debt.interest_rate == interest_rate
        assert debt.start_year == start_year

    def test_init_with_empty_dicts(self):
        """Test initialization with empty draws and paydown dictionaries"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.03, 2020)
        
        assert debt.draws == {}
        assert debt.paydown == {}
        assert debt.begin_balance == 100000
        assert debt.interest_rate == 0.03
        assert debt.start_year == 2020

    def test_init_with_none_dicts(self):
        """Test initialization with None for draws and paydown"""
        debt = ShortTermDebt('credit_line', None, None, 100000, 0.04, 2021)
        
        assert debt.draws == {}
        assert debt.paydown == {}
        assert debt.begin_balance == 100000
        assert debt.interest_rate == 0.04
        assert debt.start_year == 2021

    def test_init_invalid_name(self):
        """Test that invalid names raise ValueError"""
        with pytest.raises(ValueError, match="Short term debt name must only contain"):
            ShortTermDebt('invalid name!', {}, {}, 100000, 0.05, 2020)

    def test_init_negative_interest_rate(self):
        """Test that negative interest rate raises ValueError"""
        with pytest.raises(ValueError, match="Interest rate cannot be negative"):
            ShortTermDebt('credit_line', {}, {}, 100000, -0.05, 2020)

    def test_init_negative_draws(self):
        """Test that negative draw amounts raise ValueError"""
        draws = {2020: -50000}
        with pytest.raises(ValueError, match="Draw amount for year 2020 cannot be negative"):
            ShortTermDebt('credit_line', draws, {}, 100000, 0.05, 2020)

    def test_init_negative_paydown(self):
        """Test that negative paydown amounts raise ValueError"""
        paydown = {2020: -25000}
        with pytest.raises(ValueError, match="Paydown amount for year 2020 cannot be negative"):
            ShortTermDebt('credit_line', {}, paydown, 100000, 0.05, 2020)

    def test_defined_names(self):
        """Test that defined_names returns correct list"""
        debt = ShortTermDebt('revolving_credit', {}, {}, 100000, 0.05, 2020)
        expected_names = [
            'revolving_credit.debt_outstanding',
            'revolving_credit.draw',
            'revolving_credit.principal',
            'revolving_credit.interest'
        ]
        
        assert debt.defined_names == expected_names

    def test_get_draw(self):
        """Test get_draw method"""
        draws = {2020: 100000, 2021: 50000}
        debt = ShortTermDebt('credit_line', draws, {}, 100000, 0.05, 2020)
        
        assert debt.get_draw(2020) == 100000
        assert debt.get_draw(2021) == 50000
        assert debt.get_draw(2022) == 0.0  # Year not in draws dict
        assert debt.get_draw(2019) == 0.0  # Year before any draws

    def test_get_paydown(self):
        """Test get_paydown method"""
        paydown = {2021: 25000, 2022: 75000}
        debt = ShortTermDebt('credit_line', {}, paydown, 100000, 0.05, 2020)
        
        assert debt.get_paydown(2021) == 25000
        assert debt.get_paydown(2022) == 75000
        assert debt.get_paydown(2020) == 0.0  # Year not in paydown dict
        assert debt.get_paydown(2023) == 0.0  # Year after any paydown

    def test_get_debt_outstanding_no_activity(self):
        """Test debt outstanding with no draws or paydowns"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.05, 2020)
        
        assert debt.get_debt_outstanding(2020) == 100000
        assert debt.get_debt_outstanding(2025) == 100000

    def test_get_debt_outstanding_before_activity(self):
        """Test debt outstanding before any draws or paydowns"""
        draws = {2021: 50000}
        paydown = {2022: 25000}
        debt = ShortTermDebt('credit_line', draws, paydown, 100000, 0.05, 2020)
        
        assert debt.get_debt_outstanding(2020) == 100000
        # Test that calling for start_year - 1 returns begin_balance
        assert debt.get_debt_outstanding(2019) == 100000  # start_year - 1 = 2019
        # Test that calling before start_year - 1 raises error
        with pytest.raises(ValueError, match="Cannot calculate debt outstanding for year 2018 as it is before the start year 2020"):
            debt.get_debt_outstanding(2018)

    def test_get_debt_outstanding_before_start_year(self):
        """Test that get_debt_outstanding raises error before start year"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.05, 2020)
        
        # start_year - 1 should return begin_balance
        assert debt.get_debt_outstanding(2019) == 100000
        # Before start_year - 1 should raise error
        with pytest.raises(ValueError, match="Cannot calculate debt outstanding for year 2018 as it is before the start year 2020"):
            debt.get_debt_outstanding(2018)

    def test_get_interest_before_start_year(self):
        """Test that get_interest raises error before start year"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.05, 2020)
        
        with pytest.raises(ValueError, match="Cannot calculate interest for year 2019 as it is before the start year 2020"):
            debt.get_interest(2019)

    def test_get_interest_no_activity(self):
        """Test interest calculation with no draws or paydowns"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.05, 2020)
        
        # Interest based on begin balance
        assert debt.get_interest(2020) == 5000  # 100000 * 0.05
        assert debt.get_interest(2021) == 5000  # Same begin balance
        assert debt.get_interest(2025) == 5000  # Still same begin balance

    def test_get_interest_with_activity(self):
        """Test interest calculation with draws and paydowns"""
        draws = {2020: 100000, 2021: 50000}
        paydown = {2021: 25000, 2022: 75000}
        begin_balance = 200000
        interest_rate = 0.06
        debt = ShortTermDebt('credit_line', draws, paydown, begin_balance, interest_rate, 2020)
        
        # 2020: Interest on begin balance (200000) - first year of activity
        assert debt.get_interest(2020) == 12000  # 200000 * 0.06
        
        # 2021: Interest on previous year ending balance (300000)
        # Previous balance: 200000 + 100000 = 300000
        assert debt.get_interest(2021) == 18000  # 300000 * 0.06
        
        # 2022: Interest on previous year ending balance (325000)
        # Previous balance: 300000 + 50000 - 25000 = 325000
        assert debt.get_interest(2022) == 19500  # 325000 * 0.06
        
        # 2023: Interest on previous year ending balance (250000)
        # Previous balance: 325000 - 75000 = 250000
        assert debt.get_interest(2023) == 15000  # 250000 * 0.06

    def test_get_interest_before_activity_years(self):
        """Test interest calculation for years before activity starts"""
        draws = {2022: 50000}
        paydown = {2023: 25000}
        debt = ShortTermDebt('credit_line', draws, paydown, 100000, 0.04, 2020)
        
        # Years before activity should use begin balance
        assert debt.get_interest(2020) == 4000  # 100000 * 0.04
        assert debt.get_interest(2021) == 4000  # 100000 * 0.04

    def test_get_interest_zero_rate(self):
        """Test interest calculation with zero interest rate"""
        draws = {2020: 50000}
        debt = ShortTermDebt('credit_line', draws, {}, 100000, 0.0, 2020)
        
        assert debt.get_interest(2020) == 0.0
        assert debt.get_interest(2021) == 0.0

    def test_get_interest_high_precision(self):
        """Test interest calculation with high precision rates"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.0375, 2020)  # 3.75%
        
        assert debt.get_interest(2020) == 3750.0  # 100000 * 0.0375

    def test_complex_scenario(self):
        """Test a complex scenario with multiple years of activity"""
        draws = {2020: 200000, 2022: 100000, 2024: 50000}
        paydown = {2021: 75000, 2023: 150000, 2025: 125000}
        begin_balance = 300000
        debt = ShortTermDebt('complex_debt', draws, paydown, begin_balance, 0.05, 2020)
        
        # Year by year verification (starting from start_year)
        assert debt.get_debt_outstanding(2020) == 500000  # 300000 + 200000
        assert debt.get_debt_outstanding(2021) == 425000  # 500000 - 75000
        assert debt.get_debt_outstanding(2022) == 525000  # 425000 + 100000
        assert debt.get_debt_outstanding(2023) == 375000  # 525000 - 150000
        assert debt.get_debt_outstanding(2024) == 425000  # 375000 + 50000
        assert debt.get_debt_outstanding(2025) == 300000  # 425000 - 125000
        assert debt.get_debt_outstanding(2026) == 300000  # No more activity

    def test_zero_begin_balance(self):
        """Test functionality with zero beginning balance"""
        draws = {2020: 100000, 2021: 50000}
        paydown = {2021: 25000}
        debt = ShortTermDebt('new_line', draws, paydown, 0, 0.05, 2020)
        
        assert debt.get_debt_outstanding(2020) == 100000  # 0 + 100000
        assert debt.get_debt_outstanding(2021) == 125000  # 100000 + 50000 - 25000
        assert debt.get_debt_outstanding(2022) == 125000  # No more activity

    def test_paydown_exceeds_balance(self):
        """Test that paydowns can exceed balance (resulting in negative outstanding debt)"""
        draws = {2020: 50000}
        paydown = {2021: 200000}  # Large paydown
        debt = ShortTermDebt('test_line', draws, paydown, 100000, 0.05, 2020)
        
        assert debt.get_debt_outstanding(2020) == 150000  # 100000 + 50000
        assert debt.get_debt_outstanding(2021) == -50000  # 150000 - 200000
        assert debt.get_debt_outstanding(2022) == -50000  # No more activity

    def test_get_values_basic(self):
        """Test get_values method returns correct dictionary with interest"""
        draws = {2020: 100000, 2021: 50000}
        paydown = {2021: 25000, 2022: 75000}
        begin_balance = 200000
        interest_rate = 0.06
        debt = ShortTermDebt('revolving_credit', draws, paydown, begin_balance, interest_rate, 2020)
        
        values_2020 = debt.get_values(2020)
        expected_2020 = {
            'revolving_credit.debt_outstanding': 300000,  # 200000 + 100000
            'revolving_credit.draw': 100000,
            'revolving_credit.principal': 0,
            'revolving_credit.interest': 12000  # 200000 * 0.06
        }
        
        assert values_2020 == expected_2020
        
        values_2021 = debt.get_values(2021)
        expected_2021 = {
            'revolving_credit.debt_outstanding': 325000,  # 300000 + 50000 - 25000
            'revolving_credit.draw': 50000,
            'revolving_credit.principal': 25000,
            'revolving_credit.interest': 18000  # 300000 * 0.06 (previous year balance)
        }
        
        assert values_2021 == expected_2021
        
        values_2022 = debt.get_values(2022)
        expected_2022 = {
            'revolving_credit.debt_outstanding': 250000,  # 325000 - 75000
            'revolving_credit.draw': 0,
            'revolving_credit.principal': 75000,
            'revolving_credit.interest': 19500  # 325000 * 0.06 (previous year balance)
        }
        
        assert values_2022 == expected_2022

    def test_get_values_no_activity(self):
        """Test get_values for years without any activity"""
        draws = {2021: 50000}  # Activity starts in 2021
        paydown = {2022: 25000}
        interest_rate = 0.04
        debt = ShortTermDebt('credit_line', draws, paydown, 100000, interest_rate, 2020)
        
        values_2020 = debt.get_values(2020)
        expected_2020 = {
            'credit_line.debt_outstanding': 100000,  # Begin balance (before activity)
            'credit_line.draw': 0,
            'credit_line.principal': 0,
            'credit_line.interest': 4000  # 100000 * 0.04
        }
        
        assert values_2020 == expected_2020
        
        values_2023 = debt.get_values(2023)
        expected_2023 = {
            'credit_line.debt_outstanding': 125000,  # 100000 + 50000 - 25000
            'credit_line.draw': 0,
            'credit_line.principal': 0,
            'credit_line.interest': 5000  # 125000 * 0.04 (previous year balance)
        }
        
        assert values_2023 == expected_2023

    def test_get_values_before_start_year(self):
        """Test that get_values raises error when interest calculation fails"""
        debt = ShortTermDebt('credit_line', {}, {}, 100000, 0.05, 2020)
        
        # This should raise an error because get_interest will fail for year 2019
        with pytest.raises(ValueError, match="Cannot calculate interest for year 2019 as it is before the start year 2020"):
            debt.get_values(2019)