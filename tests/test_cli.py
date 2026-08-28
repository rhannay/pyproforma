"""Tests for the pyproforma CLI (pyproforma/cli.py)."""

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


class TestBuildApp:
    def test_returns_working_flask_app(self, tmp_path):
        path = tmp_path / "one_model.py"
        path.write_text(ONE_MODEL)
        app = build_app(path)
        client = app.test_client()
        assert client.get("/").status_code == 200
