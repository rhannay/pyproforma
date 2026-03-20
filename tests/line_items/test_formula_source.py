"""Tests for FormulaLine.formula_source property."""

from pyproforma import FormulaLine


class TestFormulaSource:

    def test_lambda_extracts_expression(self):
        line = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6)
        assert line.formula_source.startswith("lambda li, t:")
        assert "li.revenue[t] * 0.6" in line.formula_source

    def test_lambda_no_trailing_junk(self):
        # When defined as an arg, the line ends with ), label=... etc.
        # formula_source should not include those
        source = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t]).formula_source
        assert source.startswith("lambda li, t:")
        assert not source.endswith(")")

    def test_named_function(self):
        def my_formula(li, t):
            return li.revenue[t] * 0.6

        line = FormulaLine(formula=my_formula)
        source = line.formula_source
        assert "def my_formula" in source
        assert "return li.revenue[t] * 0.6" in source

    def test_no_formula_returns_none(self):
        line = FormulaLine()
        assert line.formula_source is None
