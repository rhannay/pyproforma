import pytest

from pyproforma.models.multi_line_item.debt import Debt


class TestCalculateDebtOutstandingForIssue:
    """Test cases for the _calculate_debt_outstanding_for_issue class method."""

    def test_no_debt_service_schedule(self):
        """Test that outstanding debt is 0 when there's no debt service schedule."""
        assert Debt._calculate_debt_outstanding_for_issue(None, 2024) == 0.0
        assert Debt._calculate_debt_outstanding_for_issue(None, 2025) == 0.0
        assert Debt._calculate_debt_outstanding_for_issue(None, 2030) == 0.0

    def test_empty_debt_service_schedule(self):
        """Test that outstanding debt is 0 when debt service schedule is an empty list."""
        assert Debt._calculate_debt_outstanding_for_issue([], 2024) == 0.0
        assert Debt._calculate_debt_outstanding_for_issue([], 2025) == 0.0

    def test_single_payment_outstanding(self):
        """Test outstanding debt calculation with a single future payment."""
        debt_service_schedule = [{"year": 2025, "principal": 1000.0, "interest": 50.0}]

        # Before the payment year, outstanding equals the payment amount
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2024)
            == 1000.0
        )

        # On the payment year, outstanding is 0 (payment is made at end of year)
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2025)
            == 0.0
        )

        # After the payment year, outstanding is 0
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2026)
            == 0.0
        )

    def test_multiple_payments_outstanding(self):
        """Test outstanding debt calculation with multiple future payments."""
        debt_service_schedule = [
            {"year": 2024, "principal": 500.0, "interest": 100.0},
            {"year": 2025, "principal": 600.0, "interest": 80.0},
            {"year": 2026, "principal": 700.0, "interest": 60.0},
            {"year": 2027, "principal": 800.0, "interest": 40.0},
        ]

        # Before any payments: all payments are outstanding
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2023)
            == 2600.0
        )  # 500 + 600 + 700 + 800

        # After first payment: remaining payments are outstanding
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2024)
            == 2100.0
        )  # 600 + 700 + 800

        # After second payment: remaining payments are outstanding
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2025)
            == 1500.0
        )  # 700 + 800

        # After third payment: remaining payments are outstanding
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2026)
            == 800.0
        )  # 800

        # After all payments: no outstanding debt
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2027)
            == 0.0
        )
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2028)
            == 0.0
        )

    def test_zero_principal_payments(self):
        """Test outstanding debt calculation when some principal payments are zero."""
        debt_service_schedule = [
            {"year": 2024, "principal": 0.0, "interest": 100.0},
            {"year": 2025, "principal": 1000.0, "interest": 50.0},
            {"year": 2026, "principal": 0.0, "interest": 25.0},
        ]

        # Before any payments: only non-zero principal payments count
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2023)
            == 1000.0
        )

        # After first payment (zero principal): outstanding unchanged
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2024)
            == 1000.0
        )

        # After second payment (1000 principal): outstanding is zero
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2025)
            == 0.0
        )

        # After third payment (zero principal): outstanding remains zero
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2026)
            == 0.0
        )

    def test_decimal_principal_payments(self):
        """Test outstanding debt calculation with decimal principal amounts."""
        debt_service_schedule = [
            {"year": 2024, "principal": 333.33, "interest": 50.0},
            {"year": 2025, "principal": 333.33, "interest": 40.0},
            {"year": 2026, "principal": 333.34, "interest": 30.0},
        ]

        # Test with decimal precision
        assert Debt._calculate_debt_outstanding_for_issue(
            debt_service_schedule, 2023
        ) == pytest.approx(1000.0, rel=1e-2)
        assert Debt._calculate_debt_outstanding_for_issue(
            debt_service_schedule, 2024
        ) == pytest.approx(666.67, rel=1e-2)
        assert Debt._calculate_debt_outstanding_for_issue(
            debt_service_schedule, 2025
        ) == pytest.approx(333.34, rel=1e-2)
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2026)
            == 0.0
        )

    def test_edge_case_year_boundaries(self):
        """Test edge cases around year boundaries."""
        debt_service_schedule = [{"year": 2024, "principal": 1000.0, "interest": 50.0}]

        # Test with very early and very late years
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 1900)
            == 1000.0
        )
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2100)
            == 0.0
        )

        # Test with exact payment year
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2024)
            == 0.0
        )

    def test_large_debt_amounts(self):
        """Test outstanding debt calculation with large amounts."""
        debt_service_schedule = [
            {"year": 2024, "principal": 1_000_000.0, "interest": 50_000.0},
            {"year": 2025, "principal": 2_000_000.0, "interest": 40_000.0},
        ]

        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2023)
            == 3_000_000.0
        )
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2024)
            == 2_000_000.0
        )
        assert (
            Debt._calculate_debt_outstanding_for_issue(debt_service_schedule, 2025)
            == 0.0
        )


class TestGetDebtOutstanding:
    """Test cases for the get_debt_outstanding method."""

    def test_no_debt_at_all(self):
        """Test that outstanding debt is 0 when there's no existing debt or new issues."""
        debt = Debt(
            name="test_debt",
            par_amount={},  # No new debt issues
            interest_rate=0.05,
            term=5,
            existing_debt_service=None,
        )

        assert debt.get_debt_outstanding(2024) == 0.0
        assert debt.get_debt_outstanding(2025) == 0.0

    def test_existing_debt_only(self):
        """Test outstanding debt calculation with only existing debt service."""
        existing_debt_service = [
            {"year": 2024, "principal": 1000.0, "interest": 100.0},
            {"year": 2025, "principal": 1500.0, "interest": 80.0},
            {"year": 2026, "principal": 2000.0, "interest": 60.0},
        ]

        debt = Debt(
            name="test_debt",
            par_amount={},  # No new debt issues
            interest_rate=0.05,
            term=5,
            existing_debt_service=existing_debt_service,
        )

        # Before any payments: all payments are outstanding
        assert debt.get_debt_outstanding(2023) == 4500.0  # 1000 + 1500 + 2000

        # After first payment: remaining payments are outstanding
        assert debt.get_debt_outstanding(2024) == 3500.0  # 1500 + 2000

        # After second payment: remaining payments are outstanding
        assert debt.get_debt_outstanding(2025) == 2000.0  # 2000

        # After all payments: no outstanding debt
        assert debt.get_debt_outstanding(2026) == 0.0

    def test_new_debt_issues_only(self):
        """Test outstanding debt calculation with only new debt issues."""
        debt = Debt(
            name="test_debt",
            par_amount={2024: 10000.0, 2025: 5000.0},
            interest_rate=0.05,
            term=3,  # 3-year term
            existing_debt_service=None,
        )

        # Mock interim values
        interim_values = {2024: {}, 2025: {}, 2026: {}, 2027: {}, 2028: {}}

        # Calculate debt service schedules by calling get_values for each year
        debt.get_values(interim_values, 2025)  # This builds up the ds_schedules

        # Test outstanding debt at different points
        # After 2024 issue but before 2025 issue
        debt.ds_schedules = {}  # Reset
        debt.get_values(interim_values, 2024)  # Build schedule for 2024 only
        outstanding_2024 = debt.get_debt_outstanding(2024)

        # After both issues
        debt.ds_schedules = {}  # Reset
        debt.get_values(interim_values, 2025)  # Build schedules for both years
        outstanding_2025 = debt.get_debt_outstanding(2025)

        # The 2024 issue should have some principal paid by end of 2024
        # The 2025 issue should be fully outstanding at end of 2025
        assert outstanding_2024 > 0
        assert (
            outstanding_2025 > outstanding_2024
        )  # More debt outstanding after second issue

    def test_existing_and_new_debt_combined(self):
        """Test outstanding debt calculation with both existing debt and new issues."""
        existing_debt_service = [
            {"year": 2024, "principal": 2000.0, "interest": 100.0},
            {"year": 2025, "principal": 2000.0, "interest": 80.0},
        ]

        debt = Debt(
            name="test_debt",
            par_amount={2025: 5000.0},  # New debt issue in 2025
            interest_rate=0.06,
            term=2,  # 2-year term
            existing_debt_service=existing_debt_service,
        )

        # Mock interim values
        interim_values = {2024: {}, 2025: {}, 2026: {}, 2027: {}}

        # Before any new debt is issued (2024)
        debt.get_values(interim_values, 2024)
        outstanding_2024 = debt.get_debt_outstanding(2024)
        # Should be existing debt only: 2000 (remaining payment for 2025)
        assert outstanding_2024 == 2000.0

        # After new debt is issued (2025)
        debt.ds_schedules = {}  # Reset
        debt.get_values(interim_values, 2025)
        outstanding_2025 = debt.get_debt_outstanding(2025)
        # Should be remaining existing debt (0) plus new debt outstanding
        # New debt: 5000 issued in 2025 with 2-year term, so some principal paid in 2025
        expected_new_debt = debt._calculate_debt_outstanding_for_issue(
            debt.ds_schedules[2025], 2025
        )
        assert outstanding_2025 == expected_new_debt  # Only new debt remaining

    def test_multiple_new_debt_issues(self):
        """Test outstanding debt calculation with multiple new debt issues."""
        debt = Debt(
            name="test_debt",
            par_amount={2024: 3000.0, 2025: 4000.0, 2026: 2000.0},
            interest_rate=0.04,
            term=3,
            existing_debt_service=None,
        )

        # Mock interim values
        interim_values = {2024: {}, 2025: {}, 2026: {}, 2027: {}, 2028: {}, 2029: {}}

        # Test outstanding debt after all issues
        debt.get_values(interim_values, 2026)
        outstanding_2026 = debt.get_debt_outstanding(2026)

        # Should be the sum of outstanding amounts from all three debt issues
        total_expected = 0.0
        for start_year, schedule in debt.ds_schedules.items():
            total_expected += debt._calculate_debt_outstanding_for_issue(schedule, 2026)

        assert outstanding_2026 == total_expected
        assert outstanding_2026 > 0  # Should have some debt outstanding

    def test_debt_outstanding_progression(self):
        """Test that debt outstanding decreases over time as payments are made."""
        existing_debt_service = [
            {"year": 2024, "principal": 1000.0, "interest": 50.0},
            {"year": 2025, "principal": 1000.0, "interest": 40.0},
            {"year": 2026, "principal": 1000.0, "interest": 30.0},
        ]

        debt = Debt(
            name="test_debt",
            par_amount={2024: 2000.0},  # New debt issue
            interest_rate=0.05,
            term=2,
            existing_debt_service=existing_debt_service,
        )

        # Mock interim values
        interim_values = {2023: {}, 2024: {}, 2025: {}, 2026: {}, 2027: {}}

        debt.get_values(interim_values, 2026)  # Build all schedules

        # Test that outstanding debt decreases each year
        outstanding_2023 = debt.get_debt_outstanding(2023)
        debt.get_debt_outstanding(2024)
        debt.get_debt_outstanding(2025)
        outstanding_2026 = debt.get_debt_outstanding(2026)

        # Outstanding should generally decrease over time (with possible increases when new debt is issued)
        assert (
            outstanding_2023 > outstanding_2026
        )  # Should definitely be less at the end
        assert outstanding_2026 >= 0  # Should never be negative

    def test_zero_par_amount_years(self):
        """Test outstanding debt when some years have zero par amounts."""
        debt = Debt(
            name="test_debt",
            par_amount={2024: 5000.0, 2025: 0.0, 2026: 3000.0},  # No debt in 2025
            interest_rate=0.05,
            term=2,
            existing_debt_service=None,
        )

        # Mock interim values
        interim_values = {2024: {}, 2025: {}, 2026: {}, 2027: {}, 2028: {}}

        debt.get_values(interim_values, 2026)

        # Should only have schedules for years with non-zero par amounts
        assert 2024 in debt.ds_schedules
        assert 2025 not in debt.ds_schedules  # No debt issued in 2025
        assert 2026 in debt.ds_schedules

        outstanding = debt.get_debt_outstanding(2026)

        # Should be the sum of outstanding from 2024 and 2026 issues only
        expected = debt._calculate_debt_outstanding_for_issue(
            debt.ds_schedules[2024], 2026
        ) + debt._calculate_debt_outstanding_for_issue(debt.ds_schedules[2026], 2026)
        assert outstanding == expected
