"""
Tests for the chart system: ChartSpec data layer, Charts namespace, and LineItemResult.chart().
"""

import json
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")  # headless backend — must precede any pyplot import

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel
from pyproforma.chart.chart_spec import ChartSeries, ChartSpec
from pyproforma.charts import Charts
from pyproforma.table.format_value import Format


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class SimpleModel(ProformaModel):
    revenue = FixedLine(
        values={2024: 100_000, 2025: 110_000, 2026: 121_000}, label="Revenue"
    )
    expenses = FormulaLine(
        formula=lambda li, t: li.revenue[t] * 0.6, label="Operating Expenses"
    )
    profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.expenses[t], label="Net Profit"
    )


class FormattedModel(ProformaModel):
    revenue = FixedLine(
        values={2024: 100_000, 2025: 110_000},
        label="Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    margin = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] / li.revenue[t],
        label="Margin",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.revenue[t] * 0.4,
        label="Gross Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )


@pytest.fixture
def model():
    return SimpleModel(periods=[2024, 2025, 2026])


@pytest.fixture
def formatted_model():
    return FormattedModel(periods=[2024, 2025])


# ---------------------------------------------------------------------------
# Charts namespace — existence and wiring
# ---------------------------------------------------------------------------


def test_model_has_charts_namespace(model):
    assert hasattr(model, "charts")
    assert model.charts is not None


def test_charts_namespace_type(model):
    assert isinstance(model.charts, Charts)


def test_charts_namespace_has_model_reference(model):
    assert model.charts._model is model


# ---------------------------------------------------------------------------
# Charts.line_item() — ChartSpec structure
# ---------------------------------------------------------------------------


def test_line_item_returns_chart_spec(model):
    assert isinstance(model.charts.line_item("revenue"), ChartSpec)


def test_line_item_has_one_series(model):
    assert len(model.charts.line_item("revenue").series) == 1


def test_line_item_series_is_chart_series(model):
    assert isinstance(model.charts.line_item("revenue").series[0], ChartSeries)


def test_line_item_series_label_uses_line_item_label(model):
    assert model.charts.line_item("revenue").series[0].label == "Revenue"


def test_line_item_series_x_values_match_periods(model):
    assert model.charts.line_item("revenue").series[0].x_values == [2024, 2025, 2026]


def test_line_item_series_y_values_correct_fixed(model):
    assert model.charts.line_item("revenue").series[0].y_values == [100_000, 110_000, 121_000]


def test_line_item_series_y_values_correct_formula(model):
    assert model.charts.line_item("expenses").series[0].y_values == [60_000, 66_000, 72_600]


def test_line_item_default_title_is_label(model):
    assert model.charts.line_item("revenue").title == "Revenue"


def test_line_item_custom_title(model):
    assert model.charts.line_item("revenue", title="My Revenue Chart").title == "My Revenue Chart"


def test_line_item_default_chart_type_is_line(model):
    assert model.charts.line_item("revenue").chart_type == "line"


def test_line_item_bar_chart_type(model):
    assert model.charts.line_item("revenue", chart_type="bar").chart_type == "bar"


def test_line_item_stacked_bar_chart_type(model):
    assert model.charts.line_item("revenue", chart_type="stacked_bar").chart_type == "stacked_bar"


def test_line_item_invalid_name_raises_value_error(model):
    with pytest.raises(ValueError, match="not found in model"):
        model.charts.line_item("nonexistent")


def test_line_item_no_label_falls_back_to_name_in_series_and_title():
    class NoLabelModel(ProformaModel):
        revenue = FixedLine(values={2024: 100_000})

    m = NoLabelModel(periods=[2024])
    spec = m.charts.line_item("revenue")
    assert spec.series[0].label == "revenue"
    assert spec.title == "revenue"


def test_line_item_value_format_propagated(formatted_model):
    spec = formatted_model.charts.line_item("revenue")
    assert spec.value_format is not None
    assert spec.value_format == formatted_model["revenue"].value_format


def test_line_item_value_format_defaults_to_no_decimals_when_not_explicit(model):
    # LineItem always has a value_format; unset items default to Format.NO_DECIMALS
    assert model.charts.line_item("revenue").value_format == Format.NO_DECIMALS


# ---------------------------------------------------------------------------
# Charts.line_items() — multiple series
# ---------------------------------------------------------------------------


def test_line_items_returns_chart_spec(model):
    assert isinstance(model.charts.line_items(["revenue", "profit"]), ChartSpec)


def test_line_items_series_count_matches_input(model):
    assert len(model.charts.line_items(["revenue", "expenses", "profit"]).series) == 3


def test_line_items_series_labels_in_order(model):
    spec = model.charts.line_items(["revenue", "profit"])
    assert spec.series[0].label == "Revenue"
    assert spec.series[1].label == "Net Profit"


def test_line_items_series_x_values_all_match_periods(model):
    spec = model.charts.line_items(["revenue", "expenses"])
    for series in spec.series:
        assert series.x_values == [2024, 2025, 2026]


def test_line_items_series_y_values_correct(model):
    spec = model.charts.line_items(["revenue", "expenses"])
    assert spec.series[0].y_values == [100_000, 110_000, 121_000]
    assert spec.series[1].y_values == [60_000, 66_000, 72_600]


def test_line_items_custom_title(model):
    assert model.charts.line_items(["revenue", "profit"], title="P&L").title == "P&L"


def test_line_items_default_title_is_none(model):
    assert model.charts.line_items(["revenue", "profit"]).title is None


def test_line_items_chart_type_bar(model):
    assert model.charts.line_items(["revenue"], chart_type="bar").chart_type == "bar"


def test_line_items_chart_type_stacked_bar(model):
    assert model.charts.line_items(["revenue"], chart_type="stacked_bar").chart_type == "stacked_bar"


def test_line_items_invalid_name_raises_value_error(model):
    with pytest.raises(ValueError, match="not found in model"):
        model.charts.line_items(["revenue", "nonexistent"])


# ---------------------------------------------------------------------------
# LineItemResult.chart() — convenience method
# ---------------------------------------------------------------------------


def test_line_item_result_has_chart_method(model):
    assert callable(model["revenue"].chart)


def test_line_item_result_chart_returns_chart_spec(model):
    assert isinstance(model["revenue"].chart(), ChartSpec)


def test_line_item_result_chart_values_match_direct_call(model):
    via_result = model["revenue"].chart()
    direct = model.charts.line_item("revenue")
    assert via_result.series[0].y_values == direct.series[0].y_values
    assert via_result.title == direct.title
    assert via_result.chart_type == direct.chart_type


def test_line_item_result_chart_type_parameter(model):
    assert model["revenue"].chart(chart_type="bar").chart_type == "bar"


def test_line_item_result_chart_title_parameter(model):
    assert model["revenue"].chart(title="Custom Title").title == "Custom Title"


# ---------------------------------------------------------------------------
# ChartSpec.to_dict()
# ---------------------------------------------------------------------------


def test_to_dict_returns_dict(model):
    assert isinstance(model.charts.line_item("revenue").to_dict(), dict)


def test_to_dict_has_required_keys(model):
    d = model.charts.line_item("revenue").to_dict()
    for key in ("chart_type", "title", "x_label", "y_label", "series", "value_format"):
        assert key in d


def test_to_dict_chart_type_value(model):
    assert model.charts.line_item("revenue", chart_type="bar").to_dict()["chart_type"] == "bar"


def test_to_dict_title_value(model):
    assert model.charts.line_item("revenue", title="My Chart").to_dict()["title"] == "My Chart"


def test_to_dict_series_has_required_keys(model):
    s = model.charts.line_item("revenue").to_dict()["series"][0]
    for key in ("label", "x_values", "y_values", "color"):
        assert key in s


def test_to_dict_series_label(model):
    assert model.charts.line_item("revenue").to_dict()["series"][0]["label"] == "Revenue"


def test_to_dict_series_x_values(model):
    assert model.charts.line_item("revenue").to_dict()["series"][0]["x_values"] == [2024, 2025, 2026]


def test_to_dict_series_y_values(model):
    assert model.charts.line_item("revenue").to_dict()["series"][0]["y_values"] == [100_000, 110_000, 121_000]


def test_to_dict_value_format_present_even_when_not_explicit(model):
    # value_format is always serialized — defaults to NO_DECIMALS when not explicitly set
    assert model.charts.line_item("revenue").to_dict()["value_format"] is not None


def test_to_dict_value_format_serialized_when_set(formatted_model):
    d = formatted_model.charts.line_item("revenue").to_dict()
    assert isinstance(d["value_format"], dict)


def test_to_dict_is_json_serializable(model):
    # Should not raise
    json.dumps(model.charts.line_item("revenue").to_dict())


def test_to_dict_multi_series_is_json_serializable(model):
    json.dumps(model.charts.line_items(["revenue", "expenses", "profit"]).to_dict())


# ---------------------------------------------------------------------------
# Matplotlib rendering — .figure() and .show()
# ---------------------------------------------------------------------------


def test_figure_returns_matplotlib_figure(model):
    import matplotlib.figure

    assert isinstance(model.charts.line_item("revenue").figure(), matplotlib.figure.Figure)


def test_figure_bar_chart(model):
    import matplotlib.figure

    assert isinstance(
        model.charts.line_item("revenue", chart_type="bar").figure(), matplotlib.figure.Figure
    )


def test_figure_stacked_bar_chart(model):
    import matplotlib.figure

    assert isinstance(
        model.charts.line_items(["revenue", "expenses"], chart_type="stacked_bar").figure(),
        matplotlib.figure.Figure,
    )


def test_figure_multi_series_line_chart(model):
    import matplotlib.figure

    assert isinstance(
        model.charts.line_items(["revenue", "profit"]).figure(), matplotlib.figure.Figure
    )


def test_figure_custom_figsize(model):
    fig = model.charts.line_item("revenue").figure(figsize=(8, 4))
    w, h = fig.get_size_inches()
    assert w == pytest.approx(8.0)
    assert h == pytest.approx(4.0)


def test_figure_with_value_format_applies_y_formatter(formatted_model):
    import matplotlib.ticker

    fig = formatted_model.charts.line_item("revenue").figure()
    ax = fig.axes[0]
    assert isinstance(ax.yaxis.get_major_formatter(), matplotlib.ticker.FuncFormatter)


def test_figure_always_applies_func_formatter_for_y_axis(model):
    # value_format is always set (defaults to NO_DECIMALS), so FuncFormatter is always applied
    import matplotlib.ticker

    fig = model.charts.line_item("revenue").figure()
    ax = fig.axes[0]
    assert isinstance(ax.yaxis.get_major_formatter(), matplotlib.ticker.FuncFormatter)


def test_show_calls_pyplot_show(model):
    with patch("matplotlib.pyplot.show") as mock_show:
        model.charts.line_item("revenue").show()
    mock_show.assert_called_once()


# ---------------------------------------------------------------------------
# Reserved word
# ---------------------------------------------------------------------------


def test_charts_is_in_reserved_words():
    from pyproforma.reserved_words import RESERVED_WORDS

    assert "charts" in RESERVED_WORDS


def test_charts_name_raises_on_model_definition():
    with pytest.raises(ValueError, match="'charts' is a reserved word"):

        class BadModel(ProformaModel):
            charts = FixedLine(values={2024: 1})
