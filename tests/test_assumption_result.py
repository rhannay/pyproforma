"""
Tests for scalar FixedLine behavior via LineItemResult.

Previously tested AssumptionResult; now scalar FixedLines are first-class
line items accessed uniformly through LineItemResult.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, Format, InputLine, ProformaModel
from pyproforma.line_items.line_item_result import LineItemResult


class TestScalarFixedLineResult:

    def test_getitem_returns_scalar_for_any_period(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21)

        model = M(periods=[2024, 2025])
        assert model["tax_rate"][2024] == 0.21
        assert model["tax_rate"][2025] == 0.21

    def test_getitem_raises_on_invalid_period(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21)

        model = M(periods=[2024, 2025])
        with pytest.raises(KeyError):
            model["tax_rate"][2055]

    def test_returns_line_item_result(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21)

        model = M(periods=[2024])
        assert isinstance(model["tax_rate"], LineItemResult)

    def test_label_property(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21, label="Tax Rate")

        model = M(periods=[2024])
        assert model["tax_rate"].label == "Tax Rate"

    def test_value_format_property(self):
        class M(ProformaModel):
            cogs_rate = FixedLine(value=0.35, value_format=Format.PERCENT_ONE_DECIMAL)

        model = M(periods=[2024])
        assert model["cogs_rate"].value_format == Format.PERCENT_ONE_DECIMAL

    def test_formatted_value(self):
        class M(ProformaModel):
            cogs_rate = FixedLine(value=0.354, value_format=Format.PERCENT_ONE_DECIMAL)

        model = M(periods=[2024])
        assert model["cogs_rate"].formatted_value(2024) == "35.4%"

    def test_is_input_true_for_scalar_fixed_line(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21)

        model = M(periods=[2024])
        assert model["tax_rate"].is_input(2024) is True

    def test_scalar_usable_in_formula_without_t(self):
        class M(ProformaModel):
            tax_rate = FixedLine(value=0.21)
            revenue = FixedLine(values={2024: 100_000})
            after_tax = FormulaLine(formula=lambda li, t: li.revenue[t] * (1 - li.tax_rate))

        model = M(periods=[2024])
        assert model.get_value("after_tax", 2024) == pytest.approx(79_000.0)


class TestScalarInputLineResult:

    def test_getitem_returns_scalar_for_any_period(self):
        class M(ProformaModel):
            tax_rate = InputLine()

        model = M(periods=[2024, 2025], tax_rate=0.21)
        assert model["tax_rate"][2024] == 0.21
        assert model["tax_rate"][2025] == 0.21

    def test_getitem_raises_on_invalid_period(self):
        class M(ProformaModel):
            tax_rate = InputLine()

        model = M(periods=[2024], tax_rate=0.21)
        with pytest.raises(KeyError):
            model["tax_rate"][2099]

    def test_is_input_true(self):
        class M(ProformaModel):
            tax_rate = InputLine()

        model = M(periods=[2024], tax_rate=0.21)
        assert model["tax_rate"].is_input(2024) is True
