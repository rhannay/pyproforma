"""Tests for pyproforma.explorer.config (YAML config loading)."""

import pytest

from pyproforma import FixedLine, FormulaLine, ProformaModel, ScalarInputLine, ScalarLine
from pyproforma.explorer import create_app
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
