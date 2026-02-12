"""
Tests for time offset functionality in formulas.
"""

import pytest

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel


class TestTimeOffsets:
    """Tests for time-offset subscript access in formulas."""

    def test_lookback_one_period(self):
        """Test referencing previous period value."""

        class TestModel(ProformaModel):
            base = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            # For 2025+, reference previous period
            growth = FormulaLine(
                formula=lambda: base - base[-1],
                values={2024: 0},  # First period has no previous value
            )

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.li.get("growth", 2024) == 0  # Override
        assert model.li.get("growth", 2025) == 10  # 110 - 100
        assert model.li.get("growth", 2026) == 11  # 121 - 110

    def test_lookback_two_periods(self):
        """Test referencing value two periods back."""

        class TestModel(ProformaModel):
            value = FixedLine(values={2024: 100, 2025: 110, 2026: 121, 2027: 133})
            two_period_change = FormulaLine(
                formula=lambda: value - value[-2],
                values={2024: 0, 2025: 0},  # First two periods have no value 2 periods back
            )

        model = TestModel(periods=[2024, 2025, 2026, 2027])
        assert model.li.get("two_period_change", 2024) == 0
        assert model.li.get("two_period_change", 2025) == 0
        assert model.li.get("two_period_change", 2026) == 21  # 121 - 100
        assert model.li.get("two_period_change", 2027) == 23  # 133 - 110

    def test_compound_growth(self):
        """Test compound growth using previous period reference."""

        class TestModel(ProformaModel):
            growth_rate = Assumption(value=0.1)
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            next_revenue = FormulaLine(
                formula=lambda: revenue * (1 + growth_rate),
                # No override - this calculates based on current period revenue
            )

        model = TestModel(periods=[2024, 2025, 2026])
        assert model.li.get("revenue", 2024) == 100
        # next_revenue uses current period revenue, not previous
        assert abs(model.li.get("next_revenue", 2024) - 110.0) < 0.01  # 100 * 1.1
        assert abs(model.li.get("next_revenue", 2025) - 121.0) < 0.01  # 110 * 1.1
        assert abs(model.li.get("next_revenue", 2026) - 133.1) < 0.01  # 121 * 1.1

    def test_self_reference_error_positive_offset(self):
        """Test that positive offsets raise an error."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})
            # This should fail - positive offset not allowed
            future_ref = FormulaLine(
                formula=lambda: revenue[1],  # Trying to reference future
            )

        with pytest.raises(ValueError, match="Only negative time offsets are allowed"):
            TestModel(periods=[2024, 2025])

    def test_missing_period_error(self):
        """Test that referencing a missing period raises an error."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            # This should fail for 2024 - no period 2023
            prev_revenue = FormulaLine(formula=lambda: revenue[-1])

        with pytest.raises(ValueError, match="No value found"):
            TestModel(periods=[2024])

    def test_formula_referencing_formula_with_offset(self):
        """Test formula referencing another formula's previous value."""

        class TestModel(ProformaModel):
            base = FixedLine(values={2024: 100, 2025: 110, 2026: 121})
            derived = FormulaLine(formula=lambda: base * 2)
            change = FormulaLine(
                formula=lambda: derived - derived[-1],
                values={2024: 0},  # First period override
            )

        model = TestModel(periods=[2024, 2025, 2026])
        # derived values: 200, 220, 242
        assert model.li.get("derived", 2024) == 200
        assert model.li.get("derived", 2025) == 220
        assert model.li.get("derived", 2026) == 242
        # change values
        assert model.li.get("change", 2024) == 0  # Override
        assert model.li.get("change", 2025) == 20  # 220 - 200
        assert model.li.get("change", 2026) == 22  # 242 - 220
