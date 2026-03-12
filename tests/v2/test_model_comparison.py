"""
Tests for ModelComparison.
"""

import pytest

from pyproforma.v2 import (
    Assumption,
    FixedLine,
    FormulaLine,
    ModelComparison,
    ProformaModel,
)
from pyproforma.table import Table


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def two_models():
    """Base and one comparison model with identical structure."""

    class MyModel(ProformaModel):
        expense_ratio = Assumption(value=0.6)
        revenue = FixedLine(values={2024: 100, 2025: 110})
        expenses = FormulaLine(lambda li, t: li.revenue[t] * li.expense_ratio)
        profit = FormulaLine(lambda li, t: li.revenue[t] - li.expenses[t])

    base = MyModel(periods=[2024, 2025])
    optimistic = MyModel(periods=[2024, 2025])
    return base, optimistic


@pytest.fixture
def two_models_different_revenue():
    """Base (100/110) vs optimistic (120/132)."""

    class MyModel(ProformaModel):
        expense_ratio = Assumption(value=0.6)
        revenue = FixedLine(values={2024: 100, 2025: 110})
        expenses = FormulaLine(lambda li, t: li.revenue[t] * li.expense_ratio)
        profit = FormulaLine(lambda li, t: li.revenue[t] - li.expenses[t])

    class OptModel(ProformaModel):
        expense_ratio = Assumption(value=0.6)
        revenue = FixedLine(values={2024: 120, 2025: 132})
        expenses = FormulaLine(lambda li, t: li.revenue[t] * li.expense_ratio)
        profit = FormulaLine(lambda li, t: li.revenue[t] - li.expenses[t])

    base = MyModel(periods=[2024, 2025])
    opt = OptModel(periods=[2024, 2025])
    return base, opt


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestModelComparisonInit:

    def test_basic_two_model(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt)
        assert len(cmp.models) == 2
        assert cmp.base is base

    def test_default_labels(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt)
        assert cmp.labels == ["Model 1", "Model 2"]

    def test_custom_labels(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt, labels=["Base", "Optimistic"])
        assert cmp.labels == ["Base", "Optimistic"]

    def test_labels_wrong_length_raises(self, two_models):
        base, opt = two_models
        with pytest.raises(TypeError):
            ModelComparison(base, opt, labels=["Base"])

    def test_requires_two_models(self, two_models):
        base, _ = two_models
        with pytest.raises(ValueError, match="at least 2"):
            ModelComparison(base)

    def test_common_periods_intersection(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110, 2026: 120})

        a = M(periods=[2024, 2025, 2026])
        b = M(periods=[2025, 2026])
        cmp = ModelComparison(a, b)
        assert cmp.common_periods == [2025, 2026]

    def test_no_common_periods_raises(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        a = M(periods=[2024])
        b = M(periods=[2025])
        with pytest.raises(ValueError, match="no common periods"):
            ModelComparison(a, b)

    def test_common_items_preserves_base_order(self):
        class Base(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FixedLine(values={2024: 60})
            profit = FixedLine(values={2024: 40})

        class Other(ProformaModel):
            profit = FixedLine(values={2024: 40})
            expenses = FixedLine(values={2024: 60})
            revenue = FixedLine(values={2024: 100})

        cmp = ModelComparison(Base(periods=[2024]), Other(periods=[2024]))
        assert cmp.common_items == ["revenue", "expenses", "profit"]

    def test_no_common_items_raises(self):
        class A(ProformaModel):
            foo = FixedLine(values={2024: 100})

        class B(ProformaModel):
            bar = FixedLine(values={2024: 100})

        with pytest.raises(ValueError, match="no common line items"):
            ModelComparison(A(periods=[2024]), B(periods=[2024]))

    def test_base_only_and_compare_only_items(self):
        class Base(ProformaModel):
            shared = FixedLine(values={2024: 100})
            base_only = FixedLine(values={2024: 50})

        class Other(ProformaModel):
            shared = FixedLine(values={2024: 100})
            other_only = FixedLine(values={2024: 30})

        cmp = ModelComparison(Base(periods=[2024]), Other(periods=[2024]))
        assert cmp.base_only_items == ["base_only"]
        assert cmp.compare_only_items == ["other_only"]

    def test_same_class_detected(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt)
        assert cmp._same_class is True

    def test_different_class_detected(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        assert cmp._same_class is False

    def test_three_models(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        a, b, c = M(periods=[2024]), M(periods=[2024]), M(periods=[2024])
        cmp = ModelComparison(a, b, c)
        assert len(cmp.models) == 3
        assert cmp.labels == ["Model 1", "Model 2", "Model 3"]


# ---------------------------------------------------------------------------
# compare() convenience method
# ---------------------------------------------------------------------------


class TestCompareMethod:

    def test_compare_method_returns_model_comparison(self, two_models):
        base, opt = two_models
        cmp = base.compare(opt)
        assert isinstance(cmp, ModelComparison)

    def test_compare_method_with_labels(self, two_models):
        base, opt = two_models
        cmp = base.compare(opt, labels=["Base", "Opt"])
        assert cmp.labels == ["Base", "Opt"]


# ---------------------------------------------------------------------------
# difference()
# ---------------------------------------------------------------------------


class TestDifference:

    def test_two_model_with_period_returns_float(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        assert cmp.difference("revenue", 2024) == 20.0

    def test_two_model_negative_difference(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        # opt revenue is 20 higher, so base.compare(opt) diff is +20
        cmp = ModelComparison(opt, base)  # swap: now base is the higher one
        assert cmp.difference("revenue", 2024) == -20.0

    def test_two_model_no_period_returns_dict(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.difference("revenue")
        assert result == {2024: 20.0, 2025: 22.0}

    def test_three_model_with_period_returns_dict_by_label(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        class M2(ProformaModel):
            revenue = FixedLine(values={2024: 120})

        class M3(ProformaModel):
            revenue = FixedLine(values={2024: 90})

        cmp = ModelComparison(
            M(periods=[2024]),
            M2(periods=[2024]),
            M3(periods=[2024]),
            labels=["Base", "High", "Low"],
        )
        result = cmp.difference("revenue", 2024)
        assert result == {"High": 20.0, "Low": -10.0}

    def test_three_model_no_period(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100, 2025: 110})

        class M2(ProformaModel):
            revenue = FixedLine(values={2024: 120, 2025: 130})

        cmp = ModelComparison(
            M(periods=[2024, 2025]),
            M2(periods=[2024, 2025]),
            M2(periods=[2024, 2025]),
            labels=["Base", "A", "B"],
        )
        result = cmp.difference("revenue")
        assert result["A"] == {2024: 20.0, 2025: 20.0}
        assert result["B"] == {2024: 20.0, 2025: 20.0}

    def test_invalid_item_raises(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt)
        with pytest.raises(ValueError, match="not in common_items"):
            cmp.difference("nonexistent", 2024)


# ---------------------------------------------------------------------------
# percent_difference()
# ---------------------------------------------------------------------------


class TestPercentDifference:

    def test_two_model_with_period(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.percent_difference("revenue", 2024)
        assert abs(result - 0.20) < 1e-9

    def test_returns_none_when_base_is_zero(self):
        class Base(ProformaModel):
            revenue = FixedLine(values={2024: 0})

        class Other(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        cmp = ModelComparison(Base(periods=[2024]), Other(periods=[2024]))
        assert cmp.percent_difference("revenue", 2024) is None

    def test_two_model_no_period(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.percent_difference("revenue")
        assert abs(result[2024] - 0.20) < 1e-9
        assert abs(result[2025] - (22 / 110)) < 1e-9

    def test_three_model_with_period(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        class M2(ProformaModel):
            revenue = FixedLine(values={2024: 150})

        cmp = ModelComparison(
            M(periods=[2024]),
            M2(periods=[2024]),
            M2(periods=[2024]),
            labels=["Base", "A", "B"],
        )
        result = cmp.percent_difference("revenue", 2024)
        assert abs(result["A"] - 0.5) < 1e-9
        assert abs(result["B"] - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# assumption_diff()
# ---------------------------------------------------------------------------


class TestAssumptionDiff:

    def test_same_class_returns_dict(self):
        class MyModel(ProformaModel):
            expense_ratio = Assumption(value=0.6)
            revenue = FixedLine(values={2024: 100})

        a = MyModel(periods=[2024])
        b = MyModel(periods=[2024])
        cmp = ModelComparison(a, b, labels=["Base", "Alt"])
        result = cmp.assumption_diff()
        assert "expense_ratio" in result
        assert result["expense_ratio"] == {"Base": 0.6, "Alt": 0.6}

    def test_different_class_raises(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        with pytest.raises(TypeError, match="same class"):
            cmp.assumption_diff()


# ---------------------------------------------------------------------------
# table()
# ---------------------------------------------------------------------------


class TestTable:

    def test_returns_table_instance(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.table()
        assert isinstance(result, Table)

    def test_table_has_correct_row_count(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        # header + per item: (label + 2 model rows + 1 diff row + 1 blank) * 3 items
        result = cmp.table()
        # 1 header + 3 items * (1 label + 2 model + 1 diff + 1 blank) = 1 + 15 = 16
        assert len(result.cells) == 16

    def test_table_no_difference(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.table(include_difference=False)
        # 1 header + 3 items * (1 label + 2 model + 1 blank) = 1 + 12 = 13
        assert len(result.cells) == 13

    def test_table_with_percent_difference(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.table(include_percent_difference=True)
        # 1 header + 3 items * (1 label + 2 model + 1 diff + 1 pct + 1 blank) = 1 + 18 = 19
        assert len(result.cells) == 19

    def test_table_column_count(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.table()
        # 1 label col + 2 period cols
        assert all(len(row) == 3 for row in result.cells)

    def test_table_specific_items(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        result = cmp.table(item_names=["revenue"])
        # 1 header + 1 item * (1 label + 2 model + 1 diff + 1 blank) = 6
        assert len(result.cells) == 6

    def test_table_invalid_item_raises(self, two_models_different_revenue):
        base, opt = two_models_different_revenue
        cmp = ModelComparison(base, opt)
        with pytest.raises(ValueError):
            cmp.table(item_names=["nonexistent"])


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestRepr:

    def test_repr(self, two_models):
        base, opt = two_models
        cmp = ModelComparison(base, opt)
        r = repr(cmp)
        assert "ModelComparison" in r
        assert "models=2" in r
