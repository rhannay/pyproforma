from pyproforma.models.multi_line.debt import Debt
import pytest
import math


def test_generate_debt_service_schedule_basic():
    """Test basic functionality of the debt service schedule generation."""
    # Parameters for a simple 3-year loan
    par = 1000
    interest_rate = 0.05
    start_year = 2025
    term = 3
    
    schedule = Debt._generate_debt_service_schedule(par, interest_rate, start_year, term)
    
    # Check if the schedule has the correct number of entries
    assert len(schedule) == term
    
    # Check if the years are correct
    assert [entry['year'] for entry in schedule] == [2025, 2026, 2027]
    
    # Check if the total payments sum up to the par amount (with floating point precision)
    total_principal = sum(entry['principal'] for entry in schedule)
    assert math.isclose(total_principal, par, rel_tol=1e-9)
    
    # Check if the payment amount is consistent
    first_payment = schedule[0]['principal'] + schedule[0]['interest']
    for entry in schedule[1:]:
        payment = entry['principal'] + entry['interest']
        assert math.isclose(payment, first_payment, rel_tol=1e-9)


def test_generate_debt_service_schedule_interest_calculation():
    """Test if the interest calculation is correct."""
    par = 1000
    interest_rate = 0.05
    start_year = 2025
    term = 3
    
    schedule = Debt._generate_debt_service_schedule(par, interest_rate, start_year, term)
    
    # First year interest should be exactly par * interest_rate
    assert math.isclose(schedule[0]['interest'], par * interest_rate, rel_tol=1e-9)
    
    # Calculate expected interest manually for all years
    remaining = par
    for i, entry in enumerate(schedule):
        expected_interest = remaining * interest_rate
        assert math.isclose(entry['interest'], expected_interest, rel_tol=1e-9)
        
        # Update remaining principal for next iteration
        remaining -= entry['principal']
    
    # At the end, remaining should be close to zero
    assert math.isclose(remaining, 0, abs_tol=1e-9)


def test_generate_debt_service_schedule_zero_interest():
    """Test edge case with zero interest rate."""
    par = 1000
    interest_rate = 0
    start_year = 2025
    term = 4
    
    schedule = Debt._generate_debt_service_schedule(par, interest_rate, start_year, term)
    
    # Check that we have the expected number of entries
    assert len(schedule) == term
    
    # Check that principal payments are equal (loan amount divided by term)
    expected_principal_payment = par / term
    for entry in schedule:
        assert entry['interest'] == 0  # Zero interest
        assert math.isclose(entry['principal'], expected_principal_payment)
    
    # Check the years are correct
    for i, entry in enumerate(schedule):
        assert entry['year'] == start_year + i
    
    # Verify total principal payments equal the original loan amount
    total_principal = sum(entry['principal'] for entry in schedule)
    assert math.isclose(total_principal, par)


def test_generate_debt_service_schedule_different_params():
    """Test with different parameter values."""
    test_cases = [
        {"par": 500000, "interest_rate": 0.0375, "start_year": 2025, "term": 30},
        {"par": 10000, "interest_rate": 0.12, "start_year": 2026, "term": 5},
        {"par": 25000, "interest_rate": 0.06, "start_year": 2030, "term": 10}
    ]
    
    for case in test_cases:
        schedule = Debt._generate_debt_service_schedule(
            case["par"], case["interest_rate"], case["start_year"], case["term"]
        )
        
        # Check schedule length
        assert len(schedule) == case["term"]
        
        # Check first year
        assert schedule[0]["year"] == case["start_year"]
        assert math.isclose(schedule[0]["interest"], case["par"] * case["interest_rate"], rel_tol=1e-9)
        
        # Check total principal repaid
        total_principal = sum(entry['principal'] for entry in schedule)
        assert math.isclose(total_principal, case["par"], rel_tol=1e-9)
        
        # Check annual payment consistency
        annual_payment = schedule[0]['principal'] + schedule[0]['interest']
        for entry in schedule:
            payment = entry['principal'] + entry['interest']
            assert math.isclose(payment, annual_payment, rel_tol=1e-9)


def test_generate_debt_service_schedule_amortization_calculation():
    """Test if the amortization calculation follows the expected formula."""
    par = 100000
    interest_rate = 0.04
    start_year = 2025
    term = 10
    
    schedule = Debt._generate_debt_service_schedule(par, interest_rate, start_year, term)
    
    # Calculate expected annual payment using the formula
    expected_annual_payment = (par * interest_rate) / (1 - (1 + interest_rate) ** -term)
    
    # Sum the first payment to check if it matches the expected annual payment
    actual_annual_payment = schedule[0]['principal'] + schedule[0]['interest']
    assert math.isclose(actual_annual_payment, expected_annual_payment, rel_tol=1e-9)
    
    # Calculate the entire schedule manually and compare
    remaining = par
    for i, entry in enumerate(schedule):
        expected_interest = remaining * interest_rate
        expected_principal = expected_annual_payment - expected_interest
        
        assert math.isclose(entry['interest'], expected_interest, rel_tol=1e-9)
        assert math.isclose(entry['principal'], expected_principal, rel_tol=1e-9)
        
        remaining -= expected_principal

