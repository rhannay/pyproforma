"""Tests for LineItemStat — the .stat aggregation namespace on LineItemResult."""

from pyproforma import FixedLine, Format, ProformaModel


class TestLineItemStat:

    def _model(self):
        class M(ProformaModel):
            revenue = FixedLine(
                values={2024: 100_000, 2025: 110_000, 2026: 80_000},
                value_format=Format.CURRENCY_NO_DECIMALS,
            )
        return M(periods=[2024, 2025, 2026])

    def _empty_model(self):
        class M(ProformaModel):
            revenue = FixedLine(values={})
        return M()

    # raw aggregations
    def test_min(self):
        assert self._model().revenue.stat.min() == 80_000

    def test_max(self):
        assert self._model().revenue.stat.max() == 110_000

    def test_first(self):
        assert self._model().revenue.stat.first() == 100_000

    def test_latest(self):
        assert self._model().revenue.stat.latest() == 80_000

    def test_sum(self):
        assert self._model().revenue.stat.sum() == 290_000

    def test_avg(self):
        assert abs(self._model().revenue.stat.avg() - 290_000 / 3) < 0.01

    def test_cagr(self):
        # (80_000 / 100_000)^(1/2) - 1
        expected = (80_000 / 100_000) ** (1 / 2) - 1
        assert abs(self._model().revenue.stat.cagr() - expected) < 1e-9

    def test_cagr_returns_none_when_fewer_than_two_periods(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 100_000})
        assert M(periods=[2024]).revenue.stat.cagr() is None

    def test_cagr_returns_none_when_first_is_zero(self):
        class M(ProformaModel):
            revenue = FixedLine(values={2024: 0, 2025: 100_000})
        assert M(periods=[2024, 2025]).revenue.stat.cagr() is None

    def test_returns_none_when_no_periods(self):
        s = self._empty_model().revenue.stat
        assert s.min() is None
        assert s.max() is None
        assert s.first() is None
        assert s.latest() is None
        assert s.sum() is None
        assert s.avg() is None
        assert s.cagr() is None

    # formatted aggregations
    def test_formatted_min(self):
        assert self._model().revenue.stat.formatted_min() == "$80,000"

    def test_formatted_max(self):
        assert self._model().revenue.stat.formatted_max() == "$110,000"

    def test_formatted_first(self):
        assert self._model().revenue.stat.formatted_first() == "$100,000"

    def test_formatted_latest(self):
        assert self._model().revenue.stat.formatted_latest() == "$80,000"

    def test_formatted_sum(self):
        assert self._model().revenue.stat.formatted_sum() == "$290,000"

    def test_formatted_avg(self):
        assert self._model().revenue.stat.formatted_avg() == "$96,667"

    def test_formatted_min_override_format(self):
        assert self._model().revenue.stat.formatted_min(Format.THOUSANDS_K) == "80.0K"

    def test_formatted_returns_empty_string_when_none(self):
        s = self._empty_model().revenue.stat
        assert s.formatted_min() == ""
        assert s.formatted_sum() == ""
        assert s.formatted_cagr() == ""


class TestLineItemStatRange:

    def _model(self):
        class M(ProformaModel):
            revenue = FixedLine(
                values={2024: 100_000, 2025: 110_000, 2026: 80_000},
                value_format=Format.CURRENCY_NO_DECIMALS,
            )
        return M(periods=[2024, 2025, 2026])

    def test_sum_with_start_and_end(self):
        assert self._model().revenue.stat.sum(start=2024, end=2025) == 210_000

    def test_sum_with_start_only(self):
        assert self._model().revenue.stat.sum(start=2025) == 190_000

    def test_sum_with_end_only(self):
        assert self._model().revenue.stat.sum(end=2025) == 210_000

    def test_min_with_range(self):
        # 2024–2025: min is 100_000, not 80_000
        assert self._model().revenue.stat.min(start=2024, end=2025) == 100_000

    def test_max_with_range(self):
        assert self._model().revenue.stat.max(start=2025, end=2026) == 110_000

    def test_first_with_start(self):
        assert self._model().revenue.stat.first(start=2025) == 110_000

    def test_latest_with_end(self):
        assert self._model().revenue.stat.latest(end=2025) == 110_000

    def test_avg_with_range(self):
        assert self._model().revenue.stat.avg(start=2024, end=2025) == 105_000

    def test_cagr_with_range(self):
        expected = (110_000 / 100_000) ** (1 / 1) - 1
        assert abs(self._model().revenue.stat.cagr(start=2024, end=2025) - expected) < 1e-9

    def test_formatted_sum_with_range(self):
        assert self._model().revenue.stat.formatted_sum(start=2024, end=2025) == "$210,000"

    def test_invalid_start_raises(self):
        import pytest
        with pytest.raises(ValueError, match="start 2020"):
            self._model().revenue.stat.sum(start=2020)

    def test_invalid_end_raises(self):
        import pytest
        with pytest.raises(ValueError, match="end 2099"):
            self._model().revenue.stat.sum(end=2099)
