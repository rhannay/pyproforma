"""Tests for the scenario-mode explorer app (create_scenario_app)."""

import pytest

from pyproforma import FixedLine, FormulaLine, InputLine, ProformaModel
from pyproforma.explorer import create_scenario_app
from pyproforma.explorer.components import InputGroup, StatCard


class ScenarioModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110}, label="Revenue")
    cogs = InputLine(default={2024: 50, 2025: 55}, label="COGS")
    profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.cogs[t], label="Profit")


@pytest.fixture
def base_model():
    return ScenarioModel(periods=[2024, 2025])


@pytest.fixture
def scenario_model():
    return ScenarioModel(periods=[2024, 2025], cogs={2024: 40, 2025: 45})


@pytest.fixture
def models(base_model, scenario_model):
    return {"Base": base_model, "Low COGS": scenario_model}


class TestScenarioRoutes:
    def test_root_redirects_to_first_scenario(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 302
        assert response.headers["Location"] == "/scenario/Base/"

    def test_each_scenario_index_returns_200(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        assert client.get("/scenario/Base/items").status_code == 200
        assert client.get("/scenario/Low%20COGS/items").status_code == 200

    def test_scenarios_show_different_values(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        base_html = client.get("/scenario/Base/line_item/cogs").data.decode()
        scenario_html = client.get("/scenario/Low%20COGS/line_item/cogs").data.decode()
        assert "50" in base_html
        assert "40" in scenario_html

    def test_inputs_route_not_registered(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        assert client.get("/scenario/Base/inputs").status_code == 404
        assert client.post("/scenario/Base/inputs").status_code == 404

    def test_unknown_line_item_returns_404(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        assert client.get("/scenario/Base/line_item/nonexistent").status_code == 404

    def test_min_two_models_required(self, base_model):
        with pytest.raises(ValueError, match="at least one scenario"):
            create_scenario_app({"Base": base_model})

    def test_slash_in_label_raises(self, base_model, scenario_model):
        with pytest.raises(ValueError, match="must not contain '/'"):
            create_scenario_app({"Base": base_model, "A/B": scenario_model})


class TestScenarioInputGroupDropped:
    def test_input_group_dropped_with_warning(self, models, capsys):
        views = {
            "Summary": [
                [
                    InputGroup(names=["cogs"], label="COGS Input"),
                    StatCard("profit", "Profit"),
                ],
            ],
        }
        app = create_scenario_app(models, views=views)
        captured = capsys.readouterr()
        assert "input groups are not supported in scenario mode" in captured.err
        assert "Summary" in captured.err

        client = app.test_client()
        response = client.get("/scenario/Base/view/0")
        assert response.status_code == 200
        html = response.data.decode()
        assert "COGS Input" not in html
        assert "Profit" in html

    def test_row_with_only_input_group_is_dropped_entirely(self, models):
        views = {
            "Inputs Only": [
                [InputGroup(names=["cogs"], label="COGS Input")],
                [StatCard("profit", "Profit")],
            ],
        }
        app = create_scenario_app(models, views=views)
        client = app.test_client()
        response = client.get("/scenario/Base/view/0")
        assert response.status_code == 200
        assert b"Profit" in response.data


class TestCompareRoutes:
    def test_compare_index_lists_common_items(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        response = client.get("/compare/")
        assert response.status_code == 200
        html = response.data.decode()
        assert "revenue" in html
        assert "cogs" in html
        assert "profit" in html

    def test_compare_item_shows_both_scenarios(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        response = client.get("/compare/cogs")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Base" in html
        assert "Low COGS" in html
        assert "50" in html
        assert "40" in html

    def test_compare_unknown_item_returns_404(self, models):
        app = create_scenario_app(models)
        client = app.test_client()
        assert client.get("/compare/nonexistent").status_code == 404
