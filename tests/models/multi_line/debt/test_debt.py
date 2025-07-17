from pyproforma.models.multi_line.debt import Debt
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
        

def test_debt_one_issue():
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


def test_debt_two_issues():
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


def test_debt_with_existing_schedule():
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




