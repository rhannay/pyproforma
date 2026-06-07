"""Tests for the Flask explorer app (create_app)."""

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel, ScalarInputLine, ScalarLine
from pyproforma.explorer import create_app
from pyproforma.tables.table_def import TableDef
from pyproforma.tables.row_types import HeaderRow, ItemRow
from pyproforma import ChartDef


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
