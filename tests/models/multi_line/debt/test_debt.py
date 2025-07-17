from pyproforma.models.multi_line.debt import Debt
import pytest

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
        

def test_debt_one_issue():
    debt = Debt(
        name='test',
        par_amount={2020: 1000000},
        interest_rate=0.05,
        term=30
    )
    value_dict = debt.get_values({}, 2020)
    p, i = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2020)
    assert value_dict['test.principal'] == p
    assert value_dict['test.interest'] == i

    # Test second year
    value_dict = debt.get_values(value_dict, 2021)
    p, i = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2021)
    assert value_dict['test.principal'] == p
    assert value_dict['test.interest'] == i

    # Test preivous year
    value_dict = debt.get_values(value_dict, 2019)
    assert value_dict['test.principal'] == 0.0
    assert value_dict['test.interest'] == 0.0


def test_debt_two_issues():
    """Test debt with two issues in consecutive years."""
    debt = Debt(
        name='test_multi',
        par_amount={2020: 1000000, 2021: 1500000},
        interest_rate=0.05,
        term=30
    )
    
    # Test first year (2020) - only first issuance exists
    value_dict = debt.get_values({}, 2020)
    p1, i1 = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2020)
    assert value_dict['test_multi.principal'] == p1
    assert value_dict['test_multi.interest'] == i1
    assert value_dict['test_multi.bond_proceeds'] == 1000000

    # Test second year (2021) - both issuances exist
    value_dict = debt.get_values(value_dict, 2021)
    # Values from first issuance
    p1, i1 = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2021)
    # Values from second issuance
    p2, i2 = _get_p_i(i=0.05, p=1500000, t=30, sy=2021, y=2021)
    # Total values should be sum of both issuances
    assert value_dict['test_multi.principal'] == p1 + p2
    assert value_dict['test_multi.interest'] == i1 + i2
    assert value_dict['test_multi.bond_proceeds'] == 1500000

    # Test a year before any issuance (2019)
    value_dict = debt.get_values(value_dict, 2019)
    assert value_dict['test_multi.principal'] == 0.0
    assert value_dict['test_multi.interest'] == 0.0
    assert value_dict['test_multi.bond_proceeds'] == 0.0

    # Test a future year (2022) - both issuances exist but no new bond proceeds
    value_dict = debt.get_values(value_dict, 2022)
    p1, i1 = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2022)
    p2, i2 = _get_p_i(i=0.05, p=1500000, t=30, sy=2021, y=2022)
    assert value_dict['test_multi.principal'] == p1 + p2
    assert value_dict['test_multi.interest'] == i1 + i2
    assert value_dict['test_multi.bond_proceeds'] == 0.0

    # Test 2021 again
    value_dict = debt.get_values(value_dict, 2021)
    # Values from first issuance
    p1, i1 = _get_p_i(i=0.05, p=1000000, t=30, sy=2020, y=2021)
    # Values from second issuance
    p2, i2 = _get_p_i(i=0.05, p=1500000, t=30, sy=2021, y=2021)
    # Total values should be sum of both issuances
    assert value_dict['test_multi.principal'] == p1 + p2
    assert value_dict['test_multi.interest'] == i1 + i2
    assert value_dict['test_multi.bond_proceeds'] == 1500000    
    
    


