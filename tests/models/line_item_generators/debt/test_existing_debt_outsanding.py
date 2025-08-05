import pytest
from pyproforma.models.line_item_generator.debt import Debt


class TestCalculateExistingDebtOutstanding:
    """Test cases for the _calculate_existing_debt_outstanding method."""
    
    def test_no_existing_debt_service(self):
        """Test that outstanding debt is 0 when there's no existing debt service."""
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=None
        )
        
        assert debt._calculate_existing_debt_outstanding(2024) == 0.0
        assert debt._calculate_existing_debt_outstanding(2025) == 0.0
        assert debt._calculate_existing_debt_outstanding(2030) == 0.0
    
    def test_empty_existing_debt_service(self):
        """Test that outstanding debt is 0 when existing debt service is an empty list."""
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=[]
        )
        
        assert debt._calculate_existing_debt_outstanding(2024) == 0.0
        assert debt._calculate_existing_debt_outstanding(2025) == 0.0
    
    def test_single_payment_outstanding(self):
        """Test outstanding debt calculation with a single future payment."""
        existing_debt_service = [
            {'year': 2025, 'principal': 1000.0, 'interest': 50.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        # Before the payment year, outstanding equals the payment amount
        assert debt._calculate_existing_debt_outstanding(2024) == 1000.0
        
        # On the payment year, outstanding is 0 (payment is made at end of year)
        assert debt._calculate_existing_debt_outstanding(2025) == 0.0
        
        # After the payment year, outstanding is 0
        assert debt._calculate_existing_debt_outstanding(2026) == 0.0
    
    def test_multiple_payments_outstanding(self):
        """Test outstanding debt calculation with multiple future payments."""
        existing_debt_service = [
            {'year': 2024, 'principal': 500.0, 'interest': 100.0},
            {'year': 2025, 'principal': 600.0, 'interest': 80.0},
            {'year': 2026, 'principal': 700.0, 'interest': 60.0},
            {'year': 2027, 'principal': 800.0, 'interest': 40.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        # Before any payments: all payments are outstanding
        assert debt._calculate_existing_debt_outstanding(2023) == 2600.0  # 500 + 600 + 700 + 800
        
        # After first payment: remaining payments are outstanding
        assert debt._calculate_existing_debt_outstanding(2024) == 2100.0  # 600 + 700 + 800
        
        # After second payment: remaining payments are outstanding
        assert debt._calculate_existing_debt_outstanding(2025) == 1500.0  # 700 + 800
        
        # After third payment: remaining payments are outstanding
        assert debt._calculate_existing_debt_outstanding(2026) == 800.0   # 800
        
        # After all payments: no outstanding debt
        assert debt._calculate_existing_debt_outstanding(2027) == 0.0
        assert debt._calculate_existing_debt_outstanding(2028) == 0.0
    
    def test_zero_principal_payments(self):
        """Test outstanding debt calculation when some principal payments are zero."""
        existing_debt_service = [
            {'year': 2024, 'principal': 0.0, 'interest': 100.0},
            {'year': 2025, 'principal': 1000.0, 'interest': 50.0},
            {'year': 2026, 'principal': 0.0, 'interest': 25.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        # Before any payments: only non-zero principal payments count
        assert debt._calculate_existing_debt_outstanding(2023) == 1000.0
        
        # After first payment (zero principal): outstanding unchanged
        assert debt._calculate_existing_debt_outstanding(2024) == 1000.0
        
        # After second payment (1000 principal): outstanding is zero
        assert debt._calculate_existing_debt_outstanding(2025) == 0.0
        
        # After third payment (zero principal): outstanding remains zero
        assert debt._calculate_existing_debt_outstanding(2026) == 0.0
    
    def test_decimal_principal_payments(self):
        """Test outstanding debt calculation with decimal principal amounts."""
        existing_debt_service = [
            {'year': 2024, 'principal': 333.33, 'interest': 50.0},
            {'year': 2025, 'principal': 333.33, 'interest': 40.0},
            {'year': 2026, 'principal': 333.34, 'interest': 30.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        # Test with decimal precision
        assert debt._calculate_existing_debt_outstanding(2023) == pytest.approx(1000.0, rel=1e-2)
        assert debt._calculate_existing_debt_outstanding(2024) == pytest.approx(666.67, rel=1e-2)
        assert debt._calculate_existing_debt_outstanding(2025) == pytest.approx(333.34, rel=1e-2)
        assert debt._calculate_existing_debt_outstanding(2026) == 0.0
    
    def test_edge_case_year_boundaries(self):
        """Test edge cases around year boundaries."""
        existing_debt_service = [
            {'year': 2024, 'principal': 1000.0, 'interest': 50.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        # Test with very early and very late years
        assert debt._calculate_existing_debt_outstanding(1900) == 1000.0
        assert debt._calculate_existing_debt_outstanding(2100) == 0.0
        
        # Test with exact payment year
        assert debt._calculate_existing_debt_outstanding(2024) == 0.0
    
    def test_large_debt_amounts(self):
        """Test outstanding debt calculation with large amounts."""
        existing_debt_service = [
            {'year': 2024, 'principal': 1_000_000.0, 'interest': 50_000.0},
            {'year': 2025, 'principal': 2_000_000.0, 'interest': 40_000.0}
        ]
        
        debt = Debt(
            name="test_debt",
            par_amount={2024: 1000},
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service
        )
        
        assert debt._calculate_existing_debt_outstanding(2023) == 3_000_000.0
        assert debt._calculate_existing_debt_outstanding(2024) == 2_000_000.0
        assert debt._calculate_existing_debt_outstanding(2025) == 0.0
