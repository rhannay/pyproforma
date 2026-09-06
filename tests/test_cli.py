"""Tests for the pyproforma CLI (pyproforma/cli.py)."""

from pathlib import Path

import pytest

from pyproforma.cli import build_app, load_model_from_file

ONE_MODEL = """
from pyproforma import ProformaModel, FixedLine

class MyModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110}, label="Revenue")

model = MyModel(periods=[2024, 2025])
"""

ZERO_MODEL = """
from pyproforma import ProformaModel, FixedLine

class MyModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110}, label="Revenue")
"""

TWO_MODELS = """
from pyproforma import ProformaModel, FixedLine

class MyModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110}, label="Revenue")

model = MyModel(periods=[2024, 2025])
alt_model = MyModel(periods=[2024, 2025])
"""

SCENARIO_CAPABLE_MODEL = """
from pyproforma import ProformaModel, FixedLine, ScalarInputLine

class MyModel(ProformaModel):
    revenue = FixedLine(values={2024: 100, 2025: 110}, label="Revenue")
    growth = ScalarInputLine(default=0.10, label="Growth Rate")

model = MyModel(periods=[2024, 2025])
"""


class TestLoadModelFromFile:
    def test_loads_the_single_model(self, tmp_path):
        path = tmp_path / "one_model.py"
        path.write_text(ONE_MODEL)
        result = load_model_from_file(path)
        assert result.revenue[2024] == 100

    def test_no_model_raises(self, tmp_path):
        path = tmp_path / "zero_model.py"
        path.write_text(ZERO_MODEL)
        with pytest.raises(ValueError, match="No ProformaModel instance found"):
            load_model_from_file(path)

    def test_multiple_models_raises_with_names(self, tmp_path):
        path = tmp_path / "two_models.py"
        path.write_text(TWO_MODELS)
        with pytest.raises(ValueError, match="Multiple ProformaModel instances found") as exc_info:
            load_model_from_file(path)
        assert "model" in str(exc_info.value)
        assert "alt_model" in str(exc_info.value)

    def test_nonexistent_path_raises(self, tmp_path):
        path = tmp_path / "does_not_exist.py"
        with pytest.raises(FileNotFoundError, match="No such file"):
            load_model_from_file(path)

    def test_non_python_file_raises(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("not python")
        with pytest.raises(ValueError, match="Not a Python file"):
            load_model_from_file(path)


CONFIG_YAML = """
tables:
  Revenue Table:
    rows:
      - row_type: header
      - row_type: item
        name: revenue

home_view: null
"""


class TestBuildApp:
    def test_returns_working_flask_app(self, tmp_path):
        path = tmp_path / "one_model.py"
        path.write_text(ONE_MODEL)
        app = build_app(path)
        client = app.test_client()
        assert client.get("/").status_code == 200

    def test_with_config_serves_configured_table(self, tmp_path):
        model_path = tmp_path / "one_model.py"
        model_path.write_text(ONE_MODEL)
        config_path = tmp_path / "config.yaml"
        config_path.write_text(CONFIG_YAML)

        app = build_app(model_path, config_path=config_path)
        client = app.test_client()

        # index 0 is the synthetic "All Line Items" table, 1 is "Revenue Table"
        assert client.get("/table/1").status_code == 200

    def test_relative_config_resolves_against_model_dir(self, tmp_path):
        model_dir = tmp_path / "sub"
        model_dir.mkdir()
        model_path = model_dir / "model.py"
        model_path.write_text(ONE_MODEL)
        (model_dir / "config.yaml").write_text(CONFIG_YAML)

        # A bare filename, not resolvable from the test's cwd (repo root) —
        # only correct if it's resolved against model_path's directory.
        app = build_app(model_path, config_path=Path("config.yaml"))
        client = app.test_client()
        assert client.get("/table/1").status_code == 200

    def test_with_scenarios_config_returns_scenario_app(self, tmp_path):
        model_path = tmp_path / "model.py"
        model_path.write_text(SCENARIO_CAPABLE_MODEL)
        config_path = tmp_path / "config.yaml"
        config_path.write_text("scenarios:\n  High Growth:\n    growth: 0.25\n")

        app = build_app(model_path, config_path=config_path)
        client = app.test_client()

        assert client.get("/scenario/Base/items").status_code == 200
        assert client.get("/scenario/High%20Growth/items").status_code == 200
        assert client.get("/compare/").status_code == 200
        # scenario mode has no /inputs route
        assert client.get("/scenario/Base/inputs").status_code == 404

    def test_with_compare_config_serves_compare_artifacts(self, tmp_path):
        model_path = tmp_path / "model.py"
        model_path.write_text(SCENARIO_CAPABLE_MODEL)
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "scenarios:\n"
            "  High Growth:\n"
            "    growth: 0.25\n"
            "compare:\n"
            "  tables:\n"
            "    Revenue:\n"
            "      items: [revenue]\n"
            "  charts:\n"
            "    Revenue: { item: revenue }\n"
        )

        app = build_app(model_path, config_path=config_path)
        client = app.test_client()

        assert client.get("/compare/table/0").status_code == 200
        assert client.get("/compare/chart/0").status_code == 200
