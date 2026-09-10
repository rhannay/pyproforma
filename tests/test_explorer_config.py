"""Tests for pyproforma.explorer.config (YAML config loading)."""

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel, ScalarInputLine, ScalarLine
from pyproforma.explorer import create_app, create_scenario_app
from pyproforma.explorer.components import InputGroup
from pyproforma.explorer.config import load_view_config
from pyproforma.tables.row_types import HeaderRow, ItemRow


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


TABLE_AND_CHART_YAML = """
tables:
  Income Statement:
    title: "Income Statement"
    hardcoded_color: "#1f6feb"
    rows:
      - row_type: header
      - row_type: item
        name: revenue
      - row_type: item
        name: net_income
        bold: true

charts:
  Revenue Chart:
    names: [revenue, expenses]
"""

VIEW_YAML = """
views:
  Overview:
    - - type: input_group
        names: [growth]
        label: "Growth Assumptions"
      - type: chart
        ref: Revenue Chart
    - - type: table
        ref: Income Statement

tables:
  Income Statement:
    rows:
      - row_type: header
      - row_type: item
        name: revenue

charts:
  Revenue Chart:
    names: [revenue]

home_view: Overview
"""

BAD_REF_YAML = """
views:
  Overview:
    - - type: chart
        ref: Nonexistent Chart
"""

SCENARIOS_YAML = """
scenarios:
  High Growth:
    growth: 0.20
  Low Growth:
    growth: 0.02
"""

EMPTY_SCENARIOS_YAML = """
scenarios: {}
"""

BASE_COLLISION_YAML = """
scenarios:
  Base:
    growth: 0.20
"""

COMPARE_YAML = """
scenarios:
  High Growth:
    growth: 0.20
  Low Growth:
    growth: 0.02

compare:
  tables:
    Net Income:
      items: [net_income]
      include_values: true
      include_difference: true
    Revenue Diffs:
      items: [revenue]
      include_values: false
  charts:
    Net Income:
      item: net_income
      chart_type: bar
  views:
    Summary:
      - - { type: chart, ref: Net Income }
      - - { type: table, ref: Net Income }
        - { type: table, ref: Revenue Diffs }
"""

COMPARE_BAD_VIEW_REF_YAML = """
scenarios:
  High Growth:
    growth: 0.20

compare:
  tables:
    Net Income:
      items: [net_income]
  views:
    Summary:
      - - { type: chart, ref: Nonexistent }
"""

COMPARE_WITHOUT_SCENARIOS_YAML = """
compare:
  tables:
    Net Income:
      items: [net_income]
"""

COMPARE_BAD_ITEM_YAML = """
scenarios:
  High Growth:
    growth: 0.20

compare:
  tables:
    Bogus:
      items: [not_a_line_item]
"""

COMPARE_BAD_KEY_YAML = """
scenarios:
  High Growth:
    growth: 0.20

compare:
  tables:
    Net Income:
      items: [net_income]
      include_diffs: true
"""


class TestLoadViewConfig:
    def test_table_rows_are_real_row_instances(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(TABLE_AND_CHART_YAML)
        config = load_view_config(path)
        rows = config["tables"]["Income Statement"].rows
        assert isinstance(rows[0], HeaderRow)
        assert isinstance(rows[1], ItemRow)
        assert rows[1].name == "revenue"
        assert config["tables"]["Income Statement"].title == "Income Statement"

    def test_table_hardcoded_color_parsed(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(TABLE_AND_CHART_YAML)
        config = load_view_config(path)
        assert config["tables"]["Income Statement"].hardcoded_color == "#1f6feb"

    def test_chart_passed_through_as_dict(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(TABLE_AND_CHART_YAML)
        config = load_view_config(path)
        assert config["charts"]["Revenue Chart"] == {"names": ["revenue", "expenses"]}

    def test_input_group_becomes_real_instance(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(VIEW_YAML)
        config = load_view_config(path)
        comp = config["views"]["Overview"][0][0]
        assert isinstance(comp, InputGroup)
        assert comp.names == ["growth"]
        assert comp.label == "Growth Assumptions"

    def test_stat_and_table_components_stay_as_dicts(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(VIEW_YAML)
        config = load_view_config(path)
        chart_comp = config["views"]["Overview"][0][1]
        table_comp = config["views"]["Overview"][1][0]
        assert chart_comp == {"type": "chart", "ref": "Revenue Chart"}
        assert table_comp == {"type": "table", "ref": "Income Statement"}

    def test_home_view_passed_through(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(VIEW_YAML)
        config = load_view_config(path)
        assert config["home_view"] == "Overview"

    def test_missing_ref_raises(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(BAD_REF_YAML)
        with pytest.raises(ValueError, match="Nonexistent Chart"):
            load_view_config(path)

    def test_nonexistent_path_raises(self, tmp_path):
        path = tmp_path / "does_not_exist.yaml"
        with pytest.raises(FileNotFoundError, match="No such file"):
            load_view_config(path)

    def test_non_yaml_file_raises(self, tmp_path):
        path = tmp_path / "config.txt"
        path.write_text("tables: {}")
        with pytest.raises(ValueError, match="Not a YAML file"):
            load_view_config(path)

    def test_empty_file_returns_empty_config(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("")
        config = load_view_config(path)
        assert config == {"tables": {}, "charts": {}, "views": {}, "home_view": None}


class TestLoadViewConfigIntegration:
    def test_create_app_serves_configured_routes(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(VIEW_YAML)
        config = load_view_config(path)
        app = create_app(model, **config)
        client = app.test_client()

        # state.tables prepends a synthetic "All Line Items" entry, so our
        # configured "Income Statement" table is at index 1, not 0.
        assert client.get("/").status_code == 302
        assert client.get("/view/0").status_code == 200
        assert client.get("/table/1").status_code == 200
        assert client.get("/chart/0").status_code == 200

    def test_table_row_has_line_item_href(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(VIEW_YAML)
        config = load_view_config(path)
        app = create_app(model, **config)
        client = app.test_client()

        response = client.get("/table/1")
        assert b'href="/line_item/revenue"' in response.data


class TestLoadViewConfigScenarios:
    def test_builds_model_per_scenario(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(SCENARIOS_YAML)
        config = load_view_config(path, base_model=model)
        assert set(config["models"].keys()) == {"Base", "High Growth", "Low Growth"}
        assert config["models"]["Base"] is model
        assert config["models"]["High Growth"].growth.value == 0.20
        assert config["models"]["Low Growth"].growth.value == 0.02

    def test_scenario_models_share_base_periods(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(SCENARIOS_YAML)
        config = load_view_config(path, base_model=model)
        assert config["models"]["High Growth"].periods == model.periods

    def test_no_scenarios_key_omits_models(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(TABLE_AND_CHART_YAML)
        config = load_view_config(path, base_model=model)
        assert "models" not in config

    def test_scenarios_without_base_model_raises(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(SCENARIOS_YAML)
        with pytest.raises(ValueError, match="no base model was provided"):
            load_view_config(path)

    def test_empty_scenarios_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(EMPTY_SCENARIOS_YAML)
        with pytest.raises(ValueError, match="at least one scenario"):
            load_view_config(path, base_model=model)

    def test_base_collision_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(BASE_COLLISION_YAML)
        with pytest.raises(ValueError, match="reserved for the model loaded"):
            load_view_config(path, base_model=model)


class TestLoadViewConfigCompare:
    def test_parses_compare_tables_and_charts(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_YAML)
        config = load_view_config(path, base_model=model)
        assert set(config["compare_tables"]) == {"Net Income", "Revenue Diffs"}
        assert config["compare_tables"]["Net Income"].items == ["net_income"]
        assert config["compare_tables"]["Revenue Diffs"].include_values is False
        assert config["compare_charts"]["Net Income"].item == "net_income"
        assert config["compare_charts"]["Net Income"].chart_type == "bar"

    def test_parses_compare_views(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_YAML)
        config = load_view_config(path, base_model=model)
        rows = config["compare_views"]["Summary"]
        assert rows[0] == [{"type": "chart", "ref": "Net Income"}]
        assert rows[1] == [
            {"type": "table", "ref": "Net Income"},
            {"type": "table", "ref": "Revenue Diffs"},
        ]

    def test_compare_view_unknown_ref_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_BAD_VIEW_REF_YAML)
        with pytest.raises(ValueError, match="unknown compare chart 'Nonexistent'"):
            load_view_config(path, base_model=model)

    def test_compare_without_scenarios_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_WITHOUT_SCENARIOS_YAML)
        with pytest.raises(ValueError, match="declares 'compare' but no 'scenarios'"):
            load_view_config(path, base_model=model)

    def test_compare_unknown_item_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_BAD_ITEM_YAML)
        with pytest.raises(ValueError, match="not_a_line_item"):
            load_view_config(path, base_model=model)

    def test_compare_unknown_key_raises(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_BAD_KEY_YAML)
        with pytest.raises(ValueError, match="include_diffs"):
            load_view_config(path, base_model=model)

    def test_scenarios_without_compare_still_sets_empty_dicts(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(SCENARIOS_YAML)
        config = load_view_config(path, base_model=model)
        assert config["compare_tables"] == {}
        assert config["compare_charts"] == {}
        assert config["compare_views"] == {}


class TestLoadViewConfigScenarioIntegration:
    def test_create_scenario_app_from_config(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(SCENARIOS_YAML)
        config = load_view_config(path, base_model=model)
        app = create_scenario_app(**config)
        client = app.test_client()

        assert client.get("/scenario/Base/items").status_code == 200
        assert client.get("/scenario/High%20Growth/items").status_code == 200
        assert client.get("/compare/").status_code == 200

    def test_create_scenario_app_from_config_with_compare(self, model, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(COMPARE_YAML)
        config = load_view_config(path, base_model=model)
        app = create_scenario_app(**config)
        client = app.test_client()

        assert client.get("/compare/").status_code == 200
        assert client.get("/compare/table/0").status_code == 200
        assert client.get("/compare/table/1").status_code == 200
        assert client.get("/compare/chart/0").status_code == 200
        assert client.get("/compare/view/0").status_code == 200
        html = client.get("/compare/").data.decode()
        assert "Net Income" in html
        assert "Revenue Diffs" in html
        assert "Summary" in html
