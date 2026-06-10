"""Tests for the Flask explorer app (create_app)."""

import pytest

from pyproforma import (
    ChartDef,
    FixedLine,
    FormulaLine,
    InputLine,
    ProformaModel,
    ScalarInputLine,
    ScalarLine,
)
from pyproforma.explorer import create_app
from pyproforma.explorer.components import InputGroup
from pyproforma.tables.row_types import HeaderRow, ItemRow
from pyproforma.tables.table_def import TableDef

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class SimpleModel(ProformaModel):
    revenue = FixedLine(values={2024: 1_000_000, 2025: 1_100_000}, label="Revenue")
    expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * 0.6, label="Expenses")
    net_income = FormulaLine(
        formula=lambda li, t: li.revenue[t] - li.expenses[t], label="Net Income"
    )
    rate = ScalarLine(value=0.05, label="Rate")
    growth = ScalarInputLine(default=0.10, label="Growth Rate")


@pytest.fixture
def model():
    return SimpleModel(periods=[2024, 2025])


@pytest.fixture
def tables():
    return {
        "Income Statement": TableDef(
            rows=[HeaderRow(), ItemRow("revenue"), ItemRow("expenses"), ItemRow("net_income")],
            title="Income Statement",
        )
    }


@pytest.fixture
def charts():
    return {"Revenue": ChartDef(names=["revenue"])}


@pytest.fixture
def views(tables, charts):
    return {
        "Summary": [
            [{"type": "table", "ref": "Income Statement"}],
        ]
    }


@pytest.fixture
def client(model):
    return create_app(model).test_client()


@pytest.fixture
def full_client(model, tables, charts, views):
    return create_app(model, tables=tables, charts=charts, views=views).test_client()


# ---------------------------------------------------------------------------
# Basic routes
# ---------------------------------------------------------------------------


class TestBasicRoutes:

    def test_index_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_line_item_returns_200(self, client):
        assert client.get("/line_item/revenue").status_code == 200

    def test_formula_line_item_returns_200(self, client):
        assert client.get("/line_item/net_income").status_code == 200

    def test_scalar_line_item_returns_200(self, client):
        assert client.get("/line_item/rate").status_code == 200

    def test_scalar_input_line_item_returns_200(self, client):
        assert client.get("/line_item/growth").status_code == 200

    def test_unknown_line_item_returns_404(self, client):
        assert client.get("/line_item/does_not_exist").status_code == 404

    def test_items_returns_200(self, client):
        assert client.get("/items").status_code == 200

    def test_inputs_returns_200(self, client):
        assert client.get("/inputs").status_code == 200

    def test_tag_view_returns_404_for_unknown_tag(self, client):
        assert client.get("/tag/nonexistent").status_code == 404


class TestTableAndChartRoutes:

    def test_table_view_returns_200(self, full_client):
        assert full_client.get("/table/0").status_code == 200

    def test_table_view_out_of_range_returns_404(self, full_client):
        assert full_client.get("/table/99").status_code == 404

    def test_chart_view_returns_200(self, full_client):
        assert full_client.get("/chart/0").status_code == 200

    def test_chart_view_out_of_range_returns_404(self, full_client):
        assert full_client.get("/chart/99").status_code == 404

    def test_view_returns_200(self, full_client):
        assert full_client.get("/view/0").status_code == 200

    def test_view_out_of_range_returns_404(self, full_client):
        assert full_client.get("/view/99").status_code == 404


# ---------------------------------------------------------------------------
# home_view
# ---------------------------------------------------------------------------


class TestHomeView:

    def test_home_view_redirects_to_correct_view(self, model, tables, charts, views):
        app = create_app(model, tables=tables, charts=charts, views=views, home_view="Summary")
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 302
        assert "/view/0" in response.headers["Location"]

    def test_home_view_none_shows_index(self, model):
        app = create_app(model, home_view=None)
        client = app.test_client()
        assert client.get("/").status_code == 200

    def test_items_route_accessible_when_home_view_set(self, model, tables, charts, views):
        app = create_app(model, tables=tables, charts=charts, views=views, home_view="Summary")
        client = app.test_client()
        assert client.get("/items").status_code == 200

    def test_home_view_invalid_raises_at_creation(self, model, views):
        with pytest.raises(ValueError, match="home_view 'Typo View' not found"):
            create_app(model, views=views, home_view="Typo View")

    def test_home_view_error_lists_available_views(self, model, views):
        with pytest.raises(ValueError, match="Summary"):
            create_app(model, views=views, home_view="Wrong")

    def test_home_view_with_no_views_raises(self, model):
        with pytest.raises(ValueError, match="home_view 'Summary' not found"):
            create_app(model, home_view="Summary")


# ---------------------------------------------------------------------------
# kwargs enforcement
# ---------------------------------------------------------------------------


class TestCreateAppArgs:

    def test_unknown_kwarg_raises(self, model):
        with pytest.raises(TypeError):
            create_app(model, nonexistent_option=True)

    def test_table_chart_view_positional_raises(self, model, tables):
        with pytest.raises(TypeError):
            create_app(model, tables)


# ---------------------------------------------------------------------------
# Input update
# ---------------------------------------------------------------------------


class TestInputUpdate:

    def test_post_inputs_updates_model(self, model):
        app = create_app(model)
        client = app.test_client()
        response = client.post("/inputs", data={"growth": "0.15"})
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# InputGroup component
# ---------------------------------------------------------------------------


class InputModel(ProformaModel):
    from pyproforma.table import Format as _F

    inflation = ScalarInputLine(default=0.03, label="Inflation Rate", value_format=_F.PERCENT_ONE_DECIMAL)
    revenue = FixedLine(values={2024: 100_000, 2025: 110_000}, label="Revenue")
    rate_increase = InputLine(
        default={2024: 0.05, 2025: 0.06},
        label="Rate Increase",
        value_format=_F.PERCENT_ONE_DECIMAL,
    )


@pytest.fixture
def input_model():
    return InputModel(periods=[2024, 2025])


class TestInputGroup:

    def test_default_orient_is_vertical(self):
        ig = InputGroup(names=["inflation"])
        assert ig.orient == "vertical"

    def test_invalid_orient_raises(self):
        with pytest.raises(ValueError, match="orient must be 'vertical' or 'horizontal'"):
            InputGroup(names=["inflation"], orient="sideways")

    def test_vertical_orient_accepted(self):
        ig = InputGroup(names=["inflation"], orient="vertical")
        assert ig.orient == "vertical"

    def test_horizontal_orient_accepted(self):
        ig = InputGroup(names=["inflation"], orient="horizontal")
        assert ig.orient == "horizontal"

    def test_build_scalar_input(self, input_model):
        ig = InputGroup(names=["inflation"])
        result = ig.build(input_model)
        assert result["type"] == "input_group"
        assert result["orient"] == "vertical"
        assert result["periods"] == [2024, 2025]
        assert len(result["inputs"]) == 1
        inp = result["inputs"][0]
        assert inp["name"] == "inflation"
        assert inp["label"] == "Inflation Rate"
        assert inp["is_scalar"] is True
        assert inp["value"] == pytest.approx(0.03)
        assert isinstance(inp["formatted_value"], str)

    def test_build_period_input(self, input_model):
        ig = InputGroup(names=["rate_increase"])
        result = ig.build(input_model)
        assert len(result["inputs"]) == 1
        inp = result["inputs"][0]
        assert inp["name"] == "rate_increase"
        assert inp["label"] == "Rate Increase"
        assert inp["is_scalar"] is False
        assert inp["value"] == {2024: pytest.approx(0.05), 2025: pytest.approx(0.06)}
        assert inp["periods"] == [2024, 2025]
        assert len(inp["formatted_values"]) == 2

    def test_build_mixed_inputs(self, input_model):
        ig = InputGroup(names=["inflation", "rate_increase"])
        result = ig.build(input_model)
        assert len(result["inputs"]) == 2
        assert result["inputs"][0]["is_scalar"] is True
        assert result["inputs"][1]["is_scalar"] is False

    def test_build_orient_passed_through(self, input_model):
        ig = InputGroup(names=["inflation"], orient="horizontal")
        result = ig.build(input_model)
        assert result["orient"] == "horizontal"

    def test_build_label_passed_through(self, input_model):
        ig = InputGroup(names=["inflation"], label="My Inputs")
        result = ig.build(input_model)
        assert result["label"] == "My Inputs"

    def test_build_label_none_when_not_set(self, input_model):
        ig = InputGroup(names=["inflation"])
        result = ig.build(input_model)
        assert result["label"] is None

    def test_build_invalid_name_raises(self, input_model):
        ig = InputGroup(names=["revenue"])  # FixedLine, not an input
        with pytest.raises(ValueError, match="'revenue' is not an input item"):
            ig.build(input_model)

    def test_build_unknown_name_raises(self, input_model):
        ig = InputGroup(names=["nonexistent"])
        with pytest.raises(ValueError, match="'nonexistent' is not an input item"):
            ig.build(input_model)

    def test_create_app_raises_for_two_input_groups_in_one_view(self, input_model):
        views = {
            "Bad View": [
                [
                    InputGroup(names=["inflation"]),
                    InputGroup(names=["rate_increase"]),
                ],
            ]
        }
        with pytest.raises(ValueError, match="At most one InputGroup is allowed per view"):
            create_app(input_model, views=views)

    def test_create_app_allows_one_input_group_per_view(self, input_model):
        views = {
            "View A": [[InputGroup(names=["inflation"])]],
            "View B": [[InputGroup(names=["rate_increase"])]],
        }
        app = create_app(input_model, views=views)
        assert app is not None

    def test_view_page_with_input_group_returns_200(self, input_model):
        views = {"Rates": [[InputGroup(names=["rate_increase"])]]}
        client = create_app(input_model, views=views).test_client()
        assert client.get("/view/0").status_code == 200

    def test_post_from_view_redirects_back_to_view(self, input_model):
        views = {"Rates": [[InputGroup(names=["inflation"])]]}
        client = create_app(input_model, views=views).test_client()
        response = client.post(
            "/inputs?next=/view/0",
            data={"inflation": "0.04"},
        )
        assert response.status_code == 302
        assert "/view/0" in response.headers["Location"]

    def test_partial_post_carries_forward_unsubmitted_inputs(self, input_model):
        views = {"Rates": [[InputGroup(names=["inflation"])]]}
        app = create_app(input_model, views=views)
        client = app.test_client()
        # Only submit 'inflation'; 'rate_increase' should carry forward from the model
        client.post("/inputs?next=/view/0", data={"inflation": "0.04"})
        # If rate_increase was lost, the model rebuild would fail (it has no default-less path)
        assert client.get("/view/0").status_code == 200
