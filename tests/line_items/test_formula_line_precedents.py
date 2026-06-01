"""Tests for FormulaLine.precedents property."""

import pytest

from pyproforma import FixedLine, FormulaLine


class TestFormulaLinePrecedents:

    def test_single_dependency(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
        assert line.precedents == ["revenue"]

    def test_multiple_dependencies(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
        assert line.precedents == ["revenue", "expenses"]

    def test_assumption_dependency(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] * li.tax_rate)
        assert line.precedents == ["revenue", "tax_rate"]

    def test_time_offset_reference(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t - 1] * 1.05)
        assert line.precedents == ["revenue"]

    def test_deduplication(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] + li.revenue[t - 1])
        assert line.precedents == ["revenue"]

    def test_order_preserved(self):
        line = FormulaLine(formula=lambda li, t: li.a[t] + li.b[t] + li.c[t])
        assert line.precedents == ["a", "b", "c"]

    def test_global_function_excluded(self):
        line = FormulaLine(formula=lambda li, t: max(li.revenue[t], 0))
        assert line.precedents == ["revenue"]

    def test_tag_access_excluded_from_precedents(self):
        line = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
        assert line.precedents == []

    def test_tag_references_single(self):
        line = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
        assert line.tag_references == ["revenue"]

    def test_tag_references_multiple(self):
        line = FormulaLine(formula=lambda li, t: li.tag["revenue"][t] + li.tag["cogs"][t])
        assert line.tag_references == ["revenue", "cogs"]

    def test_tag_references_deduplication(self):
        line = FormulaLine(formula=lambda li, t: li.tag["revenue"][t] + li.tag["revenue"][t])
        assert line.tag_references == ["revenue"]

    def test_tag_references_none_when_no_formula(self):
        line = FormulaLine()
        assert line.tag_references is None

    def test_tag_references_empty_when_no_tags_used(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
        assert line.tag_references == []

    def test_mixed_precedents_and_tag_references(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] - li.tag["cogs"][t])
        assert line.precedents == ["revenue"]
        assert line.tag_references == ["cogs"]

    def test_no_formula_returns_none(self):
        line = FormulaLine()
        assert line.precedents is None

    def test_named_function(self):
        def my_formula(li, t):
            return li.revenue[t] - li.expenses[t]

        line = FormulaLine(formula=my_formula)
        assert line.precedents == ["revenue", "expenses"]

    def test_named_function_with_local_var(self):
        def my_formula(li, t):
            rev = li.revenue[t]
            exp = li.expenses[t]
            return rev - exp

        line = FormulaLine(formula=my_formula)
        assert line.precedents == ["revenue", "expenses"]
