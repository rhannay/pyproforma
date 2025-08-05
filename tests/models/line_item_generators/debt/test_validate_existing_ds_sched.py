import pytest
from pyproforma.models.line_item_generator.debt import Debt


class TestValidateExistingDebtService:
    """Test cases for the _validate_existing_debt_service classmethod."""
    
    def test_valid_empty_list(self):
        """Test that an empty list is valid."""
        # Should not raise any exception
        Debt._validate_existing_debt_service([])
    
    def test_valid_none(self):
        """Test that None is treated as empty and valid."""
        # Should not raise any exception
        Debt._validate_existing_debt_service(None)
    
    def test_valid_single_entry(self):
        """Test valid single entry."""
        valid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0}
        ]
        # Should not raise any exception
        Debt._validate_existing_debt_service(valid_data)
    
    def test_valid_multiple_sequential_entries(self):
        """Test valid multiple sequential entries."""
        valid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2025, 'principal': 1000.0, 'interest': 40.0},
            {'year': 2026, 'principal': 1000.0, 'interest': 30.0}
        ]
        # Should not raise any exception
        Debt._validate_existing_debt_service(valid_data)
    
    def test_valid_with_zero_values(self):
        """Test that zero principal and interest are valid."""
        valid_data = [
            {'year': 2024, 'principal': 0.0, 'interest': 0.0},
            {'year': 2025, 'principal': 1000.0, 'interest': 50.0}
        ]
        # Should not raise any exception
        Debt._validate_existing_debt_service(valid_data)
    
    def test_valid_with_integer_values(self):
        """Test that integer values for principal and interest are valid."""
        valid_data = [
            {'year': 2024, 'principal': 1000, 'interest': 50},
            {'year': 2025, 'principal': 1000, 'interest': 40}
        ]
        # Should not raise any exception
        Debt._validate_existing_debt_service(valid_data)
    
    def test_invalid_not_list(self):
        """Test that non-list input raises ValueError."""
        with pytest.raises(ValueError, match="existing_debt_service must be a list of dictionaries"):
            Debt._validate_existing_debt_service("not a list")
        
        with pytest.raises(ValueError, match="existing_debt_service must be a list of dictionaries"):
            Debt._validate_existing_debt_service({'year': 2024, 'principal': 1000.0, 'interest': 50.0})
    
    def test_invalid_entry_not_dict(self):
        """Test that non-dictionary entries raise ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            "not a dict"
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 1 must be a dictionary"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_missing_year_key(self):
        """Test that missing 'year' key raises ValueError."""
        invalid_data = [
            {'principal': 1000.0, 'interest': 50.0}  # Missing 'year'
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0 is missing required keys: {'year'}"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_missing_principal_key(self):
        """Test that missing 'principal' key raises ValueError."""
        invalid_data = [
            {'year': 2024, 'interest': 50.0}  # Missing 'principal'
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0 is missing required keys: {'principal'}"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_missing_interest_key(self):
        """Test that missing 'interest' key raises ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0}  # Missing 'interest'
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0 is missing required keys: {'interest'}"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_missing_multiple_keys(self):
        """Test that missing multiple keys raises ValueError."""
        invalid_data = [
            {'year': 2024}  # Missing 'principal' and 'interest'
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0 is missing required keys"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_year_not_integer(self):
        """Test that non-integer year raises ValueError."""
        invalid_data = [
            {'year': 2024.5, 'principal': 1000.0, 'interest': 50.0}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'year' must be an integer"):
            Debt._validate_existing_debt_service(invalid_data)
        
        invalid_data = [
            {'year': "2024", 'principal': 1000.0, 'interest': 50.0}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'year' must be an integer"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_principal_not_number(self):
        """Test that non-numeric principal raises ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': "1000", 'interest': 50.0}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'principal' must be a number"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_interest_not_number(self):
        """Test that non-numeric interest raises ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': "50"}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'interest' must be a number"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_negative_principal(self):
        """Test that negative principal raises ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': -1000.0, 'interest': 50.0}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'principal' must be non-negative"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_negative_interest(self):
        """Test that negative interest raises ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': -50.0}
        ]
        with pytest.raises(ValueError, match="existing_debt_service entry 0: 'interest' must be non-negative"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_duplicate_years(self):
        """Test that duplicate years raise ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2024, 'principal': 500.0, 'interest': 25.0}  # Duplicate year
        ]
        with pytest.raises(ValueError, match=r"existing_debt_service contains duplicate years: \{2024\}"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_gap_in_years(self):
        """Test that gaps in years raise ValueError."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2026, 'principal': 1000.0, 'interest': 40.0}  # Gap: missing 2025
        ]
        with pytest.raises(ValueError, match="existing_debt_service years must be sequential with no gaps. Gap found between 2024 and 2026"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_invalid_multiple_gaps_in_years(self):
        """Test that multiple gaps in years raise ValueError for the first gap found."""
        invalid_data = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2027, 'principal': 1000.0, 'interest': 40.0},  # Gap: missing 2025, 2026
            {'year': 2029, 'principal': 1000.0, 'interest': 30.0}   # Gap: missing 2028
        ]
        with pytest.raises(ValueError, match="existing_debt_service years must be sequential with no gaps. Gap found between 2024 and 2027"):
            Debt._validate_existing_debt_service(invalid_data)
    
    def test_valid_unordered_input_gets_sorted(self):
        """Test that unordered input is handled correctly (internally sorted for validation)."""
        valid_data = [
            {'year': 2026, 'principal': 1000.0, 'interest': 30.0},
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2025, 'principal': 1000.0, 'interest': 40.0}
        ]
        # Should not raise any exception - method should sort internally
        Debt._validate_existing_debt_service(valid_data)
    
    def test_edge_case_large_years(self):
        """Test with large year values."""
        valid_data = [
            {'year': 2099, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2100, 'principal': 1000.0, 'interest': 40.0}
        ]
        # Should not raise any exception
        Debt._validate_existing_debt_service(valid_data)
    
    def test_edge_case_negative_years(self):
        """Test with negative year values (which should be valid integers)."""
        valid_data = [
            {'year': -2, 'principal': 1000.0, 'interest': 50.0},
            {'year': -1, 'principal': 1000.0, 'interest': 40.0}
        ]
        # Should not raise any exception - negative years are valid integers
        Debt._validate_existing_debt_service(valid_data)
