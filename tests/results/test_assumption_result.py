"""
Tests for ScalarResult — the wrapper returned by model["scalar_name"] and model.scalar_name.
"""

import pytest

from pyproforma import FixedLine, Format, FormulaLine, ProformaModel, ScalarInputLine, ScalarLine
from pyproforma.results.scalar_result import ScalarResult


class TestScalarLineResult:

    def test_getitem_returns_scalar_result(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21)

        model = M(periods=[2024, 2025])
        assert isinstance(model["tax_rate"], ScalarResult)

    def test_value_property(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21)

        model = M(periods=[2024, 2025])
        assert model["tax_rate"].value == 0.21

    def test_label_property(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21, label="Tax Rate")

        model = M(periods=[2024])
        assert model["tax_rate"].label == "Tax Rate"

    def test_value_format_property(self):
        class M(ProformaModel):
            cogs_rate = ScalarLine(value=0.35, value_format=Format.PERCENT_ONE_DECIMAL)

        model = M(periods=[2024])
        assert model["cogs_rate"].value_format == Format.PERCENT_ONE_DECIMAL

    def test_formatted_value(self):
        class M(ProformaModel):
            cogs_rate = ScalarLine(value=0.354, value_format=Format.PERCENT_ONE_DECIMAL)

        model = M(periods=[2024])
        assert model["cogs_rate"].formatted_value == "35.4%"

    def test_scalar_usable_in_formula_without_t(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21)
            revenue = FixedLine(values={2024: 100_000})
            after_tax = FormulaLine(formula=lambda li, t: li.revenue[t] * (1 - li.tax_rate))

        model = M(periods=[2024])
        assert model.get_value("after_tax", 2024) == pytest.approx(79_000.0)

    def test_float_conversion(self):
        class M(ProformaModel):
            rate = ScalarLine(value=0.05)

        model = M(periods=[2024])
        assert float(model["rate"]) == 0.05

    def test_repr(self):
        class M(ProformaModel):
            rate = ScalarLine(value=0.05)

        model = M(periods=[2024])
        r = repr(model["rate"])
        assert "rate" in r
        assert "0.05" in r

    def test_scalar_in_scalar_names(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21)

        model = M(periods=[2024])
        assert "tax_rate" in model.scalar_names
        assert "tax_rate" not in model.line_item_names

    def test_dot_notation_access(self):
        class M(ProformaModel):
            tax_rate = ScalarLine(value=0.21)

        model = M(periods=[2024])
        assert isinstance(model.tax_rate, ScalarResult)
        assert model.tax_rate.value == 0.21


class TestScalarInputLineResult:

    def test_getitem_returns_scalar_result(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine()

        model = M(periods=[2024, 2025], tax_rate=0.21)
        assert isinstance(model["tax_rate"], ScalarResult)

    def test_value_property(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine()

        model = M(periods=[2024, 2025], tax_rate=0.21)
        assert model["tax_rate"].value == 0.21

    def test_default_used_when_kwarg_omitted(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine(default=0.30)

        model = M(periods=[2024])
        assert model["tax_rate"].value == 0.30

    def test_kwarg_overrides_default(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine(default=0.30)

        model = M(periods=[2024], tax_rate=0.21)
        assert model["tax_rate"].value == 0.21

    def test_is_input_true(self):
        class M(ProformaModel):
            tax_rate = ScalarInputLine()

        model = M(periods=[2024], tax_rate=0.21)
        result = model["tax_rate"]
        assert isinstance(result, ScalarResult)
