"""
Tests for FixedLine — hardcoded period values, including explicit None periods.
"""

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel
from pyproforma.tables.row_types import HeaderRow, ItemRow, LineItemsTotalRow, TagTotalRow


class TestFixedLineClassLevel:
    def test_discovered_as_line_item(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        assert "revenue" in M._line_item_names

    def test_get_value_returns_none_for_explicit_none(self):
        line = FixedLine(values={2024: 100, 2025: None})
        assert line.get_value(2025) is None

    def test_get_value_returns_none_for_missing_period(self):
        line = FixedLine(values={2024: 100})
        assert line.get_value(2025) is None


class TestFixedLineNoneValues:
    def test_explicit_none_resolves_to_none(self):
        class M(ProformaModel):
            new_product_revenue = FixedLine(values={2024: None, 2025: 50_000})

        model = M(periods=[2024, 2025])
        assert model.new_product_revenue[2024] is None
        assert model.new_product_revenue[2025] == 50_000

    def test_missing_period_still_raises(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100})

        with pytest.raises(ValueError, match="No value defined for 'revenue' in period 2025"):
            M(periods=[2024, 2025])

    def test_tag_sum_skips_none_in_formula(self):
        class M(ProformaModel):
            core_revenue = FixedLine(values={2024: 100, 2025: 100}, tags=["revenue"])
            new_product_revenue = FixedLine(
                values={2024: None, 2025: 50}, tags=["revenue"]
            )
            total_revenue = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])

        model = M(periods=[2024, 2025])
        assert model.total_revenue[2024] == 100
        assert model.total_revenue[2025] == 150

    def test_model_tag_sum_skips_none(self):
        class M(ProformaModel):
            core_revenue = FixedLine(values={2024: 100, 2025: 100}, tags=["revenue"])
            new_product_revenue = FixedLine(
                values={2024: None, 2025: 50}, tags=["revenue"]
            )

        model = M(periods=[2024, 2025])
        assert model.tag["revenue"].sum(2024) == 100
        assert model.tag["revenue"].sum(2025) == 150

    def test_table_renders_blank_cell_for_none(self):
        class M(ProformaModel):
            new_product_revenue = FixedLine(values={2024: None, 2025: 50_000})

        model = M(periods=[2024, 2025])
        table = model.tables.build(
            [HeaderRow(), ItemRow(name="new_product_revenue")]
        )
        # Row 1 is the item row; column 1 is 2024 (None), column 2 is 2025.
        assert table[1, 1].value in (None, "")
        assert table[1, 2].value == 50_000

    def test_tag_total_row_skips_none(self):
        class M(ProformaModel):
            core_revenue = FixedLine(values={2024: 100, 2025: 100}, tags=["revenue"])
            new_product_revenue = FixedLine(
                values={2024: None, 2025: 50}, tags=["revenue"]
            )

        model = M(periods=[2024, 2025])
        table = model.tables.build(
            [HeaderRow(), TagTotalRow(tag="revenue")]
        )
        assert table[1, 1].value == 100
        assert table[1, 2].value == 150

    def test_line_items_total_row_skips_none(self):
        class M(ProformaModel):
            core_revenue = FixedLine(values={2024: 100, 2025: 100})
            new_product_revenue = FixedLine(values={2024: None, 2025: 50})

        model = M(periods=[2024, 2025])
        table = model.tables.build(
            [
                HeaderRow(),
                LineItemsTotalRow(line_item_names=["core_revenue", "new_product_revenue"]),
            ]
        )
        assert table[1, 1].value == 100
        assert table[1, 2].value == 150
