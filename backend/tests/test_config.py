"""Config boundary: `.env` is loaded explicitly and never overrides real env."""

from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture()
def config(monkeypatch, tmp_path):
    # Re-import with a clean cache so each test controls EXAM_ENV_FILE.
    monkeypatch.delenv("EXAM_ENV_FILE", raising=False)
    module = importlib.import_module("app.config")
    importlib.reload(module)
    module.__dict__["_PROJECT_ROOT"] = tmp_path
    return module


def _reload(module):
    module.load_env.cache_clear()


def test_loads_env_file_when_present(config, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("EXAM_PROBE_VALUE=from-file\n", encoding="utf-8")
    monkeypatch.delenv("EXAM_PROBE_VALUE", raising=False)
    _reload(config)

    used = config.load_env()

    assert used == env
    assert os.environ["EXAM_PROBE_VALUE"] == "from-file"


def test_real_environment_wins_over_file(config, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("EXAM_PROBE_VALUE=from-file\n", encoding="utf-8")
    monkeypatch.setenv("EXAM_PROBE_VALUE", "from-shell")
    _reload(config)

    config.load_env()

    assert os.environ["EXAM_PROBE_VALUE"] == "from-shell"


def test_returns_none_when_no_file(config):
    _reload(config)
    assert config.load_env() is None
