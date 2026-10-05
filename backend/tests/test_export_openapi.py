import json

from app.main import app
from export_openapi import TARGET, render


def test_render_matches_app_openapi():
    rendered = json.loads(render())
    assert rendered == app.openapi()


def test_export_contains_every_path():
    document = json.loads(TARGET.read_text(encoding="utf-8"))
    assert set(document["paths"]) == set(app.openapi()["paths"])
    assert document["paths"], "expected at least one path"


def test_committed_file_is_current():
    assert TARGET.read_text(encoding="utf-8") == render()
