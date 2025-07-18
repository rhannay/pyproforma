from pyproforma.models.line_item_generator.debt import Debt
import pytest
import math


def _get_p_i(i, p, t, sy, y):
    ds_schedule = Debt.generate_debt_service_schedule(
        interest_rate=i,
        par_amount=p,
        term=t,
        start_year=sy,
    )
    for row in ds_schedule:
        if row['year'] == y:
            return row['principal'], row['interest']


def _is_close(a, b, rel_tol=1e-9, abs_tol=0.0):
    """Compare two float values for approximate equality."""
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


class TestDebtParAmountsDefined:
    
    def test_debt_one_issue(self):
        debt = Debt(
            name='test',
            par_amount={2020: 1_000_000},
            interest_rate=0.05,
            term=30
        )
        years = [2020, 2021]
        value_dict = debt.get_values({}, years, 2020)
        p, i = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test.principal'], p)
        assert _is_close(value_dict['test.interest'], i)

        # Test second year
        value_dict = debt.get_values(value_dict, years, 2021)
        p, i = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        assert _is_close(value_dict['test.principal'], p)
        assert _is_close(value_dict['test.interest'], i)

        # Test preivous year
        value_dict = debt.get_values(value_dict, years, 2019)
        assert value_dict['test.principal'] == 0.0
        assert value_dict['test.interest'] == 0.0

    def test_debt_two_issues(self):
        """Test debt with two issues in consecutive years."""
        debt = Debt(
            name='test_multi',
            par_amount={2020: 1_000_000, 2021: 1_500_000},
            interest_rate=0.05,
            term=30
        )
        years = [2020, 2021, 2022]
        
        # Test first year (2020) - only first issuance exists
        value_dict = debt.get_values({}, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_multi.principal'], p1)
        assert _is_close(value_dict['test_multi.interest'], i1)
        assert value_dict['test_multi.bond_proceeds'] == 1_000_000

        # Test second year (2021) - both issuances exist
        value_dict = debt.get_values(value_dict, years, 2021)
        # Values from first issuance
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(value_dict['test_multi.principal'], p1 + p2)
        assert _is_close(value_dict['test_multi.interest'], i1 + i2)
        assert value_dict['test_multi.bond_proceeds'] == 1_500_000

        # Test a year before any issuance (2019)
        value_dict = debt.get_values(value_dict, years, 2019)
        assert value_dict['test_multi.principal'] == 0.0
        assert value_dict['test_multi.interest'] == 0.0
        assert value_dict['test_multi.bond_proceeds'] == 0.0

        # Test a future year (2022) - both issuances exist but no new bond proceeds
        value_dict = debt.get_values(value_dict, years, 2022)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2022)
        assert _is_close(value_dict['test_multi.principal'], p1 + p2)
        assert _is_close(value_dict['test_multi.interest'], i1 + i2)
        assert value_dict['test_multi.bond_proceeds'] == 0.0

        # Test 2021 again to make sure it recalculates from the ground up
        value_dict = debt.get_values(value_dict, years, 2021)
        # Values from first issuance
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(value_dict['test_multi.principal'], p1 + p2)
        assert _is_close(value_dict['test_multi.interest'], i1 + i2)
        assert value_dict['test_multi.bond_proceeds'] == 1_500_000

    def test_debt_with_existing_schedule(self):
        """Test debt with two new issues plus an existing debt service schedule."""
        # Create existing debt service schedule
        existing_ds = [
            {'year': 2020, 'principal': 50_000, 'interest': 25_000},
            {'year': 2021, 'principal': 52_500, 'interest': 22_500},
            {'year': 2022, 'principal': 55_125, 'interest': 19_875},
            {'year': 2023, 'principal': 57_881, 'interest': 17_119},
        ]
        
        # Create debt with two new issues and existing debt service
        debt = Debt(
            name='test_with_existing',
            par_amount={2020: 1_000_000, 2021: 1_500_000},
            interest_rate=0.05,
            term=30,
            existing_debt_service=existing_ds
        )
        
        years = [2019, 2020, 2021, 2022, 2023]
        
        # Test year before any activity (2019) - should be zero
        value_dict = debt.get_values({}, years, 2019)
        assert value_dict['test_with_existing.principal'] == 0.0
        assert value_dict['test_with_existing.interest'] == 0.0
        assert value_dict['test_with_existing.bond_proceeds'] == 0.0
        
        # Test first year (2020) - first issuance + existing schedule
        value_dict = debt.get_values(value_dict, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_with_existing.principal'], p1 + 50_000)
        assert _is_close(value_dict['test_with_existing.interest'], i1 + 25_000)
        assert value_dict['test_with_existing.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - both issuances + existing schedule
        value_dict = debt.get_values(value_dict, years, 2021)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        assert _is_close(value_dict['test_with_existing.principal'], p1 + p2 + 52_500)
        assert _is_close(value_dict['test_with_existing.interest'], i1 + i2 + 22_500)
        assert value_dict['test_with_existing.bond_proceeds'] == 1_500_000
        
        # Test future year (2022) - both issuances + existing schedule, no new proceeds
        value_dict = debt.get_values(value_dict, years, 2022)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2022)
        assert _is_close(value_dict['test_with_existing.principal'], p1 + p2 + 55_125)
        assert _is_close(value_dict['test_with_existing.interest'], i1 + i2 + 19_875)
        assert value_dict['test_with_existing.bond_proceeds'] == 0.0
        
        # Test last year of existing schedule (2023)
        value_dict = debt.get_values(value_dict, years, 2023)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2023)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2023)
        assert _is_close(value_dict['test_with_existing.principal'], p1 + p2 + 57_881)
        assert _is_close(value_dict['test_with_existing.interest'], i1 + i2 + 17_119)
        assert value_dict['test_with_existing.bond_proceeds'] == 0.0


class TestDebtParamsFromValueMatrix:
    
    def test_debt_par_amounts_from_value_matrix(self):
        """Test debt where par_amount is a string reference to a value in interim_values_by_year."""
        # Create a debt object with par_amount as a string reference
        debt = Debt(
            name='test_from_matrix',
            par_amount='par_amount',  # This string refers to a key in interim_values_by_year
            interest_rate=0.05,
            term=30
        )
        
        years = [2020, 2021, 2022]
        
        # Create interim_values_by_year with par_amount values for specific years
        interim_values = {
            2020: {'par_amount': 1_000_000},
            2021: {'par_amount': 1_500_000},
            2022: {'par_amount': 0}  # No new issuance in 2022
        }
        
        # Test first year (2020)
        value_dict = debt.get_values(interim_values, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_from_matrix.principal'], p1)
        assert _is_close(value_dict['test_from_matrix.interest'], i1)
        assert value_dict['test_from_matrix.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - both issuances exist
        value_dict = debt.get_values(interim_values, years, 2021)
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(value_dict['test_from_matrix.principal'], p1 + p2)
        assert _is_close(value_dict['test_from_matrix.interest'], i1 + i2)
        assert value_dict['test_from_matrix.bond_proceeds'] == 1_500_000
        
        # Test third year (2022) - both previous issuances exist but no new bond proceeds
        value_dict = debt.get_values(interim_values, years, 2022)
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2022)
        # Total values should be sum of both issuances, with no new bond proceeds
        assert _is_close(value_dict['test_from_matrix.principal'], p1 + p2)
        assert _is_close(value_dict['test_from_matrix.interest'], i1 + i2)
        assert value_dict['test_from_matrix.bond_proceeds'] == 0
        
    def test_all_debt_params_from_value_matrix(self):
        """Test debt where all parameters (par_amount, interest_rate, term) are string references."""
        # Create a debt object with all parameters as string references
        debt = Debt(
            name='test_all_params',
            par_amount='par_amount',      # String reference to par_amount in interim values
            interest_rate='interest_rate', # String reference to interest_rate in interim values
            term='term'                   # String reference to term in interim values
        )
        
        years = [2020, 2021, 2022]
        
        # Create interim_values_by_year with all parameter values for different years
        interim_values = {
            2020: {
                'par_amount': 1_000_000,
                'interest_rate': 0.05,
                'term': 30
            },
            2021: {
                'par_amount': 1_500_000,
                'interest_rate': 0.06,  # Different rate for 2021 issuance
                'term': 25              # Different term for 2021 issuance
            },
            2022: {
                'par_amount': 0,        # No new issuance
                'interest_rate': 0.07,  # Not used since par_amount is 0
                'term': 20              # Not used since par_amount is 0
            }
        }
        
        # Test first year (2020) - only first issuance exists
        value_dict = debt.get_values(interim_values, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_all_params.principal'], p1)
        assert _is_close(value_dict['test_all_params.interest'], i1)
        assert value_dict['test_all_params.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - both issuances exist
        value_dict = debt.get_values(interim_values, years, 2021)
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance (2021) - note the different rate and term
        p2, i2 = _get_p_i(i=0.06, p=1_500_000, t=25, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(value_dict['test_all_params.principal'], p1 + p2)
        assert _is_close(value_dict['test_all_params.interest'], i1 + i2)
        assert value_dict['test_all_params.bond_proceeds'] == 1_500_000
        
        # Test third year (2022) - both previous issuances exist but no new bond proceeds
        value_dict = debt.get_values(interim_values, years, 2022)
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.06, p=1_500_000, t=25, sy=2021, y=2022)
        # Total values should be sum of both issuances, with no new bond proceeds
        assert _is_close(value_dict['test_all_params.principal'], p1 + p2)
        assert _is_close(value_dict['test_all_params.interest'], i1 + i2)
        assert value_dict['test_all_params.bond_proceeds'] == 0


    def test_interest_rate_missing(self):
        """Test debt where one of the parameters is missing in interim_values_by_year."""
        # Create a debt object with par_amount as a string reference
        debt = Debt(
            name='test_missing_param',
            par_amount='par_amount',  # This string refers to a key in interim_values_by_year
            interest_rate='interest_rate',  # This will be missing for 2021
            term=30  # Fixed term
        )
        
        years = [2020, 2021, 2022]
        
        # Create interim_values_by_year with par_amount values but missing interest_rate for 2021
        interim_values = {
            2020: {'par_amount': 1_000_000, 'interest_rate': 0.05},
            2021: {'par_amount': 1_500_000},  # Missing interest_rate
            2022: {'par_amount': 0}  # No new issuance
        }
        
        # Test first year (2020)
        value_dict = debt.get_values(interim_values, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_missing_param.principal'], p1)
        assert _is_close(value_dict['test_missing_param.interest'], i1)
        assert value_dict['test_missing_param.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - should raise an error due to missing interest_rate
        with pytest.raises(ValueError) as excinfo:
            debt.get_values(interim_values, years, 2021)
        assert "Could not find interest rate 'interest_rate' for year 2021 in interim values" in str(excinfo.value)

    def test_par_amount_missing(self):
        """Test debt where par_amount is missing in interim_values_by_year."""
        # Create a debt object with par_amount as a string reference
        debt = Debt(
            name='test_missing_par',
            par_amount='par_amount',  # This string refers to a key in interim_values_by_year
            interest_rate=0.05,  # Fixed interest rate
            term=30  # Fixed term
        )
        
        years = [2020, 2021, 2022]
        
        # Create interim_values_by_year with missing par_amount for 2021
        interim_values = {
            2020: {'par_amount': 1_000_000},
            2021: {},  # Missing par_amount
            2022: {'par_amount': 0}  # No new issuance
        }
        
        # Test first year (2020)
        value_dict = debt.get_values(interim_values, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_missing_par.principal'], p1)
        assert _is_close(value_dict['test_missing_par.interest'], i1)
        assert value_dict['test_missing_par.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - should raise an error due to missing par_amount
        with pytest.raises(ValueError) as excinfo:
            debt.get_values(interim_values, years, 2021)
        assert "Could not find par amount 'par_amount' for year 2021 in interim values" in str(excinfo.value)


class TestDebtParAmountNone:
    
    def test_debt_with_second_par_amount_none(self):
        """Test debt where the first par_amount is a number but the second is None."""
        # Create a debt object with mixed par amounts
        debt = Debt(
            name='test_with_none',
            par_amount={2020: 1_000_000, 2021: 0},  # First amount is a number, second is zero (not None)
            interest_rate=0.05,
            term=30
        )
        
        years = [2020, 2021, 2022]
        
        # Test first year (2020) - only first issuance should exist
        value_dict = debt.get_values({}, years, 2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(value_dict['test_with_none.principal'], p1)
        assert _is_close(value_dict['test_with_none.interest'], i1)
        assert value_dict['test_with_none.bond_proceeds'] == 1_000_000
        
        # Test second year (2021) - should still only have the first issuance
        # No new issuance should occur because the par_amount is None
        value_dict = debt.get_values(value_dict, years, 2021)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Only the first issuance should contribute to principal and interest
        assert _is_close(value_dict['test_with_none.principal'], p1)
        assert _is_close(value_dict['test_with_none.interest'], i1)
        # No bond proceeds since par_amount is None for this year
        assert value_dict['test_with_none.bond_proceeds'] == 0.0
        
        # Test future year (2022) - should still only have the first issuance
        value_dict = debt.get_values(value_dict, years, 2022)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        assert _is_close(value_dict['test_with_none.principal'], p1)
        assert _is_close(value_dict['test_with_none.interest'], i1)
        assert value_dict['test_with_none.bond_proceeds'] == 0.0



