from pyproforma.generators.debt import Debt, generate_debt_service_schedule
import pytest

@pytest.fixture
def expected_schedule_1mm():
    return [
        {'year': 2020, 'principal': 15051.44, 'interest': 50000.00},
        {'year': 2021, 'principal': 15804.01, 'interest': 49247.43},
        {'year': 2022, 'principal': 16594.21, 'interest': 48457.23},
        {'year': 2023, 'principal': 17423.92, 'interest': 47627.52},
        {'year': 2024, 'principal': 18295.11, 'interest': 46756.32},
        {'year': 2025, 'principal': 19209.87, 'interest': 45841.57},
        {'year': 2026, 'principal': 20170.36, 'interest': 44881.07},
        {'year': 2027, 'principal': 21178.88, 'interest': 43872.55},
        {'year': 2028, 'principal': 22237.82, 'interest': 42813.61},
        {'year': 2029, 'principal': 23349.72, 'interest': 41701.72},
        {'year': 2030, 'principal': 24517.20, 'interest': 40534.23},
        {'year': 2031, 'principal': 25743.06, 'interest': 39308.37},
        {'year': 2032, 'principal': 27030.21, 'interest': 38021.22},
        {'year': 2033, 'principal': 28381.73, 'interest': 36669.71},
        {'year': 2034, 'principal': 29800.81, 'interest': 35250.62},
        {'year': 2035, 'principal': 31290.85, 'interest': 33760.58},
        {'year': 2036, 'principal': 32855.40, 'interest': 32196.04},
        {'year': 2037, 'principal': 34498.16, 'interest': 30553.27},
        {'year': 2038, 'principal': 36223.07, 'interest': 28828.36},
        {'year': 2039, 'principal': 38034.23, 'interest': 27017.21},
        {'year': 2040, 'principal': 39935.94, 'interest': 25115.50},
        {'year': 2041, 'principal': 41932.74, 'interest': 23118.70},
        {'year': 2042, 'principal': 44029.37, 'interest': 21022.06},
        {'year': 2043, 'principal': 46230.84, 'interest': 18820.59},
        {'year': 2044, 'principal': 48542.38, 'interest': 16509.05},
        {'year': 2045, 'principal': 50969.50, 'interest': 14081.93},
        {'year': 2046, 'principal': 53517.98, 'interest': 11533.46},
        {'year': 2047, 'principal': 56193.88, 'interest': 8857.56},
        {'year': 2048, 'principal': 59003.57, 'interest': 6047.87},
        {'year': 2049, 'principal': 61953.75, 'interest': 3097.69},
    ]


class TestDebt:
    def test_init(self, expected_schedule_1mm):
        par_amounts = {2020: 1_000_000, 2021: 1_200_000}
        interest_rate = 0.05
        term = 30
        
        debt = Debt('debt', par_amounts, interest_rate, term)
        
        assert isinstance(debt.schedules, dict)
        assert len(debt.schedules) == len(par_amounts)
        
        for year, schedule in debt.schedules.items():
            assert isinstance(schedule, list)
            assert len(schedule) == term
            
            # check expected schedule from excel
            expected_schedule = generate_debt_service_schedule(par_amounts[year], interest_rate, year, term)
            for expected, actual in zip(expected_schedule, schedule):
                assert abs(expected['principal'] - actual['principal']) < 1e-2
                assert abs(expected['interest'] - actual['interest']) < 1e-2
                assert expected['year'] == actual['year']
    


    def test_get_total_principal_and_interest(self, expected_schedule_1mm):
        par_amounts = {2020: 1_000_000, 2021: 1_000_000}
        interest_rate = 0.05
        term = 30
        
        debt = Debt('debt', par_amounts, interest_rate, term)
        total_principal_2020 = debt.get_total_principal(2020) 
        series_2020_year_1_principal = expected_schedule_1mm[0]['principal']
        expected_2020 = series_2020_year_1_principal
        assert abs(total_principal_2020 - expected_2020) < 1e-2 
        series_2020_year_2_principal = expected_schedule_1mm[1]['principal']
        series_2021_year_1_principal = expected_schedule_1mm[0]['principal']
        expected_2021 = series_2020_year_2_principal + series_2021_year_1_principal
        total_principal_2021 = debt.get_total_principal(2021)
        assert abs(total_principal_2021 - expected_2021) < 1e-2

        total_interest_2020 = debt.get_total_interest(2020)
        series_2020_year_1_interest = expected_schedule_1mm[0]['interest']
        expected_interest_2020 = series_2020_year_1_interest
        assert abs(total_interest_2020 - expected_interest_2020) < 1e-2

        series_2020_year_2_interest = expected_schedule_1mm[1]['interest']
        series_2021_year_1_interest = expected_schedule_1mm[0]['interest']
        expected_interest_2021 = series_2020_year_2_interest + series_2021_year_1_interest
        total_interest_2021 = debt.get_total_interest(2021)
        assert abs(total_interest_2021 - expected_interest_2021) < 1e-2

        values_dict = debt.get_values(2020)
        assert isinstance(values_dict, dict)
        assert len(values_dict) == 3
        assert 'debt.principal' in values_dict
        assert 'debt.interest' in values_dict
        assert 'debt.bond_proceeds' in values_dict
        assert abs(values_dict[f'{debt.name}.principal'] - total_principal_2020) < 1e-2
        assert abs(values_dict[f'{debt.name}.interest'] - total_interest_2020) < 1e-2
        assert values_dict[f'{debt.name}.bond_proceeds'] == par_amounts[2020]

        # out of range returns 0
        assert debt.get_total_principal(1990) == 0.0
        assert debt.get_total_principal(2090) == 0.0

    def test_get_total_principal_with_existing_debt_service(self):
        """Test that get_total_principal properly incorporates existing debt service"""
        existing_debt = [
            {'year': 2020, 'principal': 50000.0, 'interest': 25000.0},
            {'year': 2021, 'principal': 55000.0, 'interest': 22000.0}
        ]
        
        par_amounts = {2021: 1_000_000}  # New debt starts in 2021
        interest_rate = 0.05
        term = 3
        
        debt = Debt('test_debt', par_amounts, interest_rate, term, existing_debt_service=existing_debt)
        
        # Year 2020: Only existing debt service
        assert abs(debt.get_total_principal(2020) - 50000.0) < 1e-6
        
        # Year 2021: Existing debt service + new debt
        debt_without_existing = Debt('new_only', par_amounts, interest_rate, term)
        new_debt_principal_2021 = debt_without_existing.get_total_principal(2021)
        expected_total_2021 = 55000.0 + new_debt_principal_2021
        assert abs(debt.get_total_principal(2021) - expected_total_2021) < 1e-6
        
        # Year 2022: Only new debt (no existing debt service for this year)
        new_debt_principal_2022 = debt_without_existing.get_total_principal(2022)
        assert abs(debt.get_total_principal(2022) - new_debt_principal_2022) < 1e-6
        
        # Year with no debt at all
        assert debt.get_total_principal(2025) == 0.0

    def test_get_total_interest_with_existing_debt_service(self):
        """Test that get_total_interest properly incorporates existing debt service"""
        existing_debt = [
            {'year': 2020, 'principal': 50000.0, 'interest': 25000.0},
            {'year': 2021, 'principal': 55000.0, 'interest': 22000.0}
        ]
        
        par_amounts = {2021: 1_000_000}  # New debt starts in 2021
        interest_rate = 0.05
        term = 3
        
        debt = Debt('test_debt', par_amounts, interest_rate, term, existing_debt_service=existing_debt)
        
        # Year 2020: Only existing debt service
        assert abs(debt.get_total_interest(2020) - 25000.0) < 1e-6
        
        # Year 2021: Existing debt service + new debt
        debt_without_existing = Debt('new_only', par_amounts, interest_rate, term)
        new_debt_interest_2021 = debt_without_existing.get_total_interest(2021)
        expected_total_2021 = 22000.0 + new_debt_interest_2021
        assert abs(debt.get_total_interest(2021) - expected_total_2021) < 1e-6
        
        # Year 2022: Only new debt (no existing debt service for this year)
        new_debt_interest_2022 = debt_without_existing.get_total_interest(2022)
        assert abs(debt.get_total_interest(2022) - new_debt_interest_2022) < 1e-6
        
        # Year with no debt at all
        assert debt.get_total_interest(2025) == 0.0

    def test_get_values_with_existing_debt_service(self):
        """Test that get_values properly incorporates existing debt service in returned values"""
        existing_debt = [
            {'year': 2020, 'principal': 75000.0, 'interest': 30000.0}
        ]
        
        par_amounts = {2020: 500000}  # New debt also starts in 2020
        interest_rate = 0.04
        term = 5
        
        debt = Debt('combined_debt', par_amounts, interest_rate, term, existing_debt_service=existing_debt)
        
        # Get values for year 2020 (should include both existing and new debt)
        values = debt.get_values(2020)
        
        # Calculate expected values
        debt_without_existing = Debt('new_only', par_amounts, interest_rate, term)
        new_principal = debt_without_existing.get_total_principal(2020)
        new_interest = debt_without_existing.get_total_interest(2020)
        
        expected_principal = 75000.0 + new_principal
        expected_interest = 30000.0 + new_interest
        
        assert abs(values['combined_debt.principal'] - expected_principal) < 1e-6
        assert abs(values['combined_debt.interest'] - expected_interest) < 1e-6
        assert values['combined_debt.bond_proceeds'] == 500000  # Bond proceeds not affected by existing debt

    def test_multiple_existing_debt_years_integration(self):
        """Test integration with multiple years of existing debt service"""
        existing_debt = [
            {'year': 2019, 'principal': 100000.0, 'interest': 40000.0},
            {'year': 2020, 'principal': 110000.0, 'interest': 35000.0},
            {'year': 2021, 'principal': 120000.0, 'interest': 30000.0}
        ]
        
        par_amounts = {2020: 2_000_000, 2021: 1_500_000}  # Multiple new debt issues
        interest_rate = 0.05
        term = 4
        
        debt = Debt('multi_debt', par_amounts, interest_rate, term, existing_debt_service=existing_debt)
        
        # Create comparable debt without existing debt service
        debt_new_only = Debt('new_only', par_amounts, interest_rate, term)
        
        # Test year 2019: Only existing debt
        assert abs(debt.get_total_principal(2019) - 100000.0) < 1e-6
        assert abs(debt.get_total_interest(2019) - 40000.0) < 1e-6
        
        # Test year 2020: Existing + first new debt issue
        new_principal_2020 = debt_new_only.get_total_principal(2020)
        new_interest_2020 = debt_new_only.get_total_interest(2020)
        expected_principal_2020 = 110000.0 + new_principal_2020
        expected_interest_2020 = 35000.0 + new_interest_2020
        
        assert abs(debt.get_total_principal(2020) - expected_principal_2020) < 1e-6
        assert abs(debt.get_total_interest(2020) - expected_interest_2020) < 1e-6
        
        # Test year 2021: Existing + both new debt issues
        new_principal_2021 = debt_new_only.get_total_principal(2021)
        new_interest_2021 = debt_new_only.get_total_interest(2021)
        expected_principal_2021 = 120000.0 + new_principal_2021
        expected_interest_2021 = 30000.0 + new_interest_2021
        
        assert abs(debt.get_total_principal(2021) - expected_principal_2021) < 1e-6
        assert abs(debt.get_total_interest(2021) - expected_interest_2021) < 1e-6
        
        # Test year 2022: Only new debt (no existing debt service)
        new_principal_2022 = debt_new_only.get_total_principal(2022)
        new_interest_2022 = debt_new_only.get_total_interest(2022)
        
        assert abs(debt.get_total_principal(2022) - new_principal_2022) < 1e-6
        assert abs(debt.get_total_interest(2022) - new_interest_2022) < 1e-6


class TestGenerateServiceDebtSchedule:
    def test_init(self, expected_schedule_1mm):
        par = 1_000_000
        interest_rate = 0.05
        start_year = 2020
        term = 30
        schedule = generate_debt_service_schedule(par, interest_rate, start_year, term)
        
        assert isinstance(schedule, list)
        assert len(schedule) == term
        
        years = [entry['year'] for entry in schedule]
        assert years == list(range(start_year, start_year + term))
        
        for expected, actual in zip(expected_schedule_1mm, schedule):
            assert abs(expected['principal'] - actual['principal']) < 1e-2, f"Principal mismatch for year {expected['year']}"
            assert abs(expected['interest'] - actual['interest']) < 1e-2, f"Interest mismatch for year {expected['year']}"
            assert expected['year'] == actual['year'], f"Year mismatch: expected {expected['year']}, got {actual['year']}"


class TestDebtExistingDebtService:
    """Test validation of existing_debt_service parameter"""
    
    def test_valid_existing_debt_service(self):
        """Test that valid existing_debt_service is accepted"""
        valid_existing = [
            {'year': 2020, 'principal': 100.0, 'interest': 50.0},
            {'year': 2021, 'principal': 110.0, 'interest': 45.0},
            {'year': 2022, 'principal': 120.0, 'interest': 40.0}
        ]
        
        # Should not raise any exception
        debt = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=valid_existing
        )
        assert debt.name == "test_debt"
    
    def test_empty_existing_debt_service(self):
        """Test that empty list or None is accepted"""
        # Empty list
        debt1 = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=[]
        )
        assert debt1.name == "test_debt"
        
        # None (default)
        debt2 = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=None
        )
        assert debt2.name == "test_debt"
    
    def test_negative_principal_raises_error(self):
        """Test that negative principal raises ValueError"""
        invalid_negative_principal = [
            {'year': 2020, 'principal': -100.0, 'interest': 50.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*principal.*cannot be negative"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_negative_principal
            )
    
    def test_negative_interest_raises_error(self):
        """Test that negative interest raises ValueError"""
        invalid_negative_interest = [
            {'year': 2020, 'principal': 100.0, 'interest': -50.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*interest.*cannot be negative"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_negative_interest
            )
    
    def test_zero_values_allowed(self):
        """Test that zero principal and interest are allowed"""
        zero_values = [
            {'year': 2020, 'principal': 0.0, 'interest': 0.0}
        ]
        
        # Should not raise any exception
        debt = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=zero_values
        )
        assert debt.name == "test_debt"
    
    def test_non_sequential_years_raises_error(self):
        """Test that non-sequential years raise ValueError"""
        invalid_gap = [
            {'year': 2020, 'principal': 100.0, 'interest': 50.0},
            {'year': 2022, 'principal': 120.0, 'interest': 40.0}  # Gap: missing 2021
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service years must be sequential.*Gap found between 2020 and 2022"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_gap
            )
    
    def test_duplicate_years_raises_error(self):
        """Test that duplicate years raise ValueError"""
        invalid_duplicate = [
            {'year': 2020, 'principal': 100.0, 'interest': 50.0},
            {'year': 2020, 'principal': 110.0, 'interest': 45.0}  # Duplicate year
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service has duplicate years.*2020"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_duplicate
            )
    
    def test_missing_required_keys_raises_error(self):
        """Test that missing required keys raise ValueError"""
        # Missing 'interest'
        invalid_missing_interest = [
            {'year': 2020, 'principal': 100.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*missing required keys.*interest"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_missing_interest
            )
        
        # Missing 'principal'
        invalid_missing_principal = [
            {'year': 2020, 'interest': 50.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*missing required keys.*principal"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_missing_principal
            )
        
        # Missing 'year'
        invalid_missing_year = [
            {'principal': 100.0, 'interest': 50.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*missing required keys.*year"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_missing_year
            )
    
    def test_non_dict_entry_raises_error(self):
        """Test that non-dict entries raise ValueError"""
        invalid_non_dict = [
            "not a dict"
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*must be a dict"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_non_dict
            )
    
    def test_non_integer_year_raises_error(self):
        """Test that non-integer year raises ValueError"""
        invalid_year_type = [
            {'year': "2020", 'principal': 100.0, 'interest': 50.0}
        ]
        
        with pytest.raises(ValueError, match="existing_debt_service.*year.*must be an integer"):
            Debt(
                name="test_debt",
                par_amounts={2023: 1000000},
                interest_rate=0.05,
                term=10,
                existing_debt_service=invalid_year_type
            )
    
    def test_single_year_entry(self):
        """Test that single year entry works (no sequential check needed)"""
        single_year = [
            {'year': 2020, 'principal': 100.0, 'interest': 50.0}
        ]
        
        # Should not raise any exception
        debt = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=single_year
        )
        assert debt.name == "test_debt"
    
    def test_multiple_valid_entries(self):
        """Test multiple valid entries in different orders"""
        # Unordered but sequential when sorted
        unordered_valid = [
            {'year': 2022, 'principal': 120.0, 'interest': 40.0},
            {'year': 2020, 'principal': 100.0, 'interest': 50.0},
            {'year': 2021, 'principal': 110.0, 'interest': 45.0}
        ]
        
        # Should not raise any exception
        debt = Debt(
            name="test_debt",
            par_amounts={2023: 1000000},
            interest_rate=0.05,
            term=10,
            existing_debt_service=unordered_valid
        )
        assert debt.name == "test_debt"
    
    def test_existing_debt_service_incorporated_in_totals(self):
        """Test that existing debt service is properly added to principal and interest totals"""
        existing_debt = [
            {'year': 2020, 'principal': 100.0, 'interest': 50.0},
            {'year': 2021, 'principal': 110.0, 'interest': 45.0},
            {'year': 2022, 'principal': 120.0, 'interest': 40.0}
        ]
        
        # Create debt with both existing debt service and new debt
        debt = Debt(
            name="combined_debt",
            par_amounts={2021: 1000000},  # New debt issued in 2021
            interest_rate=0.05,
            term=3,
            existing_debt_service=existing_debt
        )
        
        # Test year 2020 (only existing debt)
        assert abs(debt.get_total_principal(2020) - 100.0) < 1e-6
        assert abs(debt.get_total_interest(2020) - 50.0) < 1e-6
        
        # Test year 2021 (existing debt + new debt)
        # First, get what new debt alone would be
        debt_new_only = Debt("new_only", {2021: 1000000}, 0.05, 3)
        new_principal_2021 = debt_new_only.get_total_principal(2021)
        new_interest_2021 = debt_new_only.get_total_interest(2021)
        
        # Combined should be existing + new
        expected_total_principal_2021 = 110.0 + new_principal_2021
        expected_total_interest_2021 = 45.0 + new_interest_2021
        
        assert abs(debt.get_total_principal(2021) - expected_total_principal_2021) < 1e-6
        assert abs(debt.get_total_interest(2021) - expected_total_interest_2021) < 1e-6
        
        # Test year 2022 (existing debt + new debt second payment)
        new_principal_2022 = debt_new_only.get_total_principal(2022)
        new_interest_2022 = debt_new_only.get_total_interest(2022)
        
        expected_total_principal_2022 = 120.0 + new_principal_2022
        expected_total_interest_2022 = 40.0 + new_interest_2022
        
        assert abs(debt.get_total_principal(2022) - expected_total_principal_2022) < 1e-6
        assert abs(debt.get_total_interest(2022) - expected_total_interest_2022) < 1e-6
        
        # Test year 2023 (only new debt, no existing debt service)
        new_principal_2023 = debt_new_only.get_total_principal(2023)
        new_interest_2023 = debt_new_only.get_total_interest(2023)
        
        assert abs(debt.get_total_principal(2023) - new_principal_2023) < 1e-6
        assert abs(debt.get_total_interest(2023) - new_interest_2023) < 1e-6
        
        # Test year with no debt at all
        assert debt.get_total_principal(2024) == 0.0
        assert debt.get_total_interest(2024) == 0.0
    
    def test_existing_debt_service_only(self):
        """Test debt with only existing debt service (no new debt)"""
        existing_debt = [
            {'year': 2020, 'principal': 200.0, 'interest': 75.0},
            {'year': 2021, 'principal': 220.0, 'interest': 65.0}
        ]
        
        # Create debt with only existing debt service (empty par_amounts)
        debt = Debt(
            name="existing_only",
            par_amounts={},  # No new debt
            interest_rate=0.05,
            term=10,
            existing_debt_service=existing_debt
        )
        
        # Should return exactly the existing debt service values
        assert debt.get_total_principal(2020) == 200.0
        assert debt.get_total_interest(2020) == 75.0
        assert debt.get_total_principal(2021) == 220.0
        assert debt.get_total_interest(2021) == 65.0
        
        # Years not in existing debt service should return 0
        assert debt.get_total_principal(2022) == 0.0
        assert debt.get_total_interest(2022) == 0.0

