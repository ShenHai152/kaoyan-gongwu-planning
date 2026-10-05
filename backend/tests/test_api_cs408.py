from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domains.kaoyan.cs408_etl import load_cs408_governance, load_cs408_units
from app.domains.kaoyan.cs408_parsing import (
    parse_conflicts,
    parse_school,
    parse_subject_changes,
)
from app.main import app, get_session
from tests.test_kaoyan_cs408 import SAMPLE, SAMPLE_CHANGES, SAMPLE_CONFLICTS


def make_client(engine) -> TestClient:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        units, lines = parse_school(SAMPLE, source_file="001-深圳大学.json")
        load_cs408_units(session, units, lines)
        load_cs408_governance(
            session,
            parse_conflicts(SAMPLE_CONFLICTS, source_file="x.json"),
            parse_subject_changes(SAMPLE_CHANGES, source_file="x.json"),
        )
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app)


def test_units_endpoint(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/cs408/units", params={"school": "深圳大学"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["college"] == "人工智能学院"
    assert body[0]["subject_class"] == "11408"


def test_units_filter_by_subject_class(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/cs408/units",
        params={"school": "深圳大学", "subject_class": "22408"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_year_lines_endpoint(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/cs408/year-lines", params={"school": "深圳大学", "year": 2026}
    )
    assert r.status_code == 200
    body = r.json()
    assert {item["college"] for item in body} == {"人工智能学院", "计算机与软件学院"}
    ai = next(item for item in body if item["college"] == "人工智能学院")
    assert ai["line_value"] == 335.0


def test_subject_changes_and_conflicts_endpoints(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/cs408/subject-changes", params={"school": "测试大学"})
    assert r.status_code == 200
    assert r.json()[0]["new_subject"] == "数二"

    r = client.get("/api/kaoyan/cs408/conflicts", params={"school": "测试大学"})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_empty_results_are_200(engine):
    client = make_client(engine)
    for path in ("units", "year-lines", "subject-changes", "conflicts"):
        r = client.get(f"/api/kaoyan/cs408/{path}", params={"school": "不存在的大学"})
        assert r.status_code == 200
        assert r.json() == []
