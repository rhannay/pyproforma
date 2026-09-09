"""Smoke tests for example models and Flask explorer apps."""

import importlib.util
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _load_module(path):
    spec = importlib.util.spec_from_file_location("_example", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestExampleModels:
    def test_coffee_shop_model_loads(self):
        mod = _load_module(EXAMPLES_DIR / "coffee_shop" / "model.py")
        assert len(mod.model.periods) > 0

    def test_water_utility_model_loads(self):
        mod = _load_module(EXAMPLES_DIR / "water_utility" / "model.py")
        assert len(mod.model.periods) > 0


class TestExampleApps:
    @pytest.fixture
    def coffee_shop_client(self):
        from pyproforma.explorer import create_app
        mod = _load_module(EXAMPLES_DIR / "coffee_shop" / "model.py")
        return create_app(mod.model).test_client()

    @pytest.fixture
    def water_utility_client(self):
        from pyproforma.explorer import create_app
        mod = _load_module(EXAMPLES_DIR / "water_utility" / "model.py")
        return create_app(mod.model).test_client()

    def test_coffee_shop_index(self, coffee_shop_client):
        assert coffee_shop_client.get("/").status_code == 200

    def test_coffee_shop_line_item(self, coffee_shop_client):
        assert coffee_shop_client.get("/line_item/gross_profit").status_code == 200

    def test_coffee_shop_scalar_line_item(self, coffee_shop_client):
        assert coffee_shop_client.get("/line_item/food_cogs_rate").status_code == 200

    def test_water_utility_index(self, water_utility_client):
        assert water_utility_client.get("/").status_code == 200

    def test_water_utility_line_item(self, water_utility_client):
        assert water_utility_client.get("/line_item/dscr").status_code == 200

    def test_water_utility_inputs(self, water_utility_client):
        assert water_utility_client.get("/inputs").status_code == 200


class TestExampleScenarioConfig:
    @pytest.fixture
    def water_utility_scenario_client(self):
        from pyproforma.cli import build_app

        app = build_app(
            EXAMPLES_DIR / "water_utility" / "model.py",
            config_path=EXAMPLES_DIR / "water_utility" / "config_w_scenario.yaml",
        )
        return app.test_client()

    def test_scenario_index(self, water_utility_scenario_client):
        c = water_utility_scenario_client
        assert c.get("/scenario/Base/items").status_code == 200
        assert c.get("/scenario/Lower%20Rate%20Increases/items").status_code == 200
        # home_view is set, so the bare scenario root redirects to it
        assert c.get("/scenario/Base/", follow_redirects=True).status_code == 200

    def test_compare_overview_and_artifacts(self, water_utility_scenario_client):
        c = water_utility_scenario_client
        assert c.get("/compare/").status_code == 200
        assert c.get("/compare/items").status_code == 200
        assert c.get("/compare/table/0").status_code == 200
        assert c.get("/compare/table/2").status_code == 200
        assert c.get("/compare/chart/0").status_code == 200
        assert c.get("/compare/chart/1").status_code == 200
        assert c.get("/compare/view/0").status_code == 200
        assert c.get("/compare/view/1").status_code == 200
