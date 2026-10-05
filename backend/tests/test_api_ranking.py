from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domains.kaoyan.etl import load_admission_lines
from app.main import app, get_session
from tests.test_kaoyan_ranking import _line


def make_client(engine) -> TestClient:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        load_admission_lines(
            session,
            [
                _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, is_985=True),
                _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
                _line(school_name="丙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300, zone="B"),
            ],
        )
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app)


def test_ranking_endpoint(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/rankings/program",
        params={"year": 2026, "program_code": "085404"},
    )
    assert r.status_code == 200
    body = r.json()
    assert [row["school_name"] for row in body["rows"]] == ["甲大学", "乙大学", "丙大学"]
    assert [row["rank"] for row in body["rows"]] == [1, 2, 3]
    assert body["position"] is None
    assert body["disclaimer"]


def test_ranking_with_score_position(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/rankings/program",
        params={"year": 2026, "program_code": "085404", "score": 350},
    )
    body = r.json()
    assert body["position"]["provisional_rank"] == 2
    assert body["position"]["schools_passing"] == 2


def test_ranking_filter_985(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/rankings/program",
        params={"year": 2026, "program_code": "085404", "is_985": True},
    )
    body = r.json()
    assert [row["school_name"] for row in body["rows"]] == ["甲大学"]


def test_ranking_empty_is_200(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/rankings/program",
        params={"year": 1999, "program_code": "085404"},
    )
    assert r.status_code == 200
    assert r.json()["rows"] == []


def test_ranking_requires_program(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/rankings/program", params={"year": 2026})
    assert r.status_code == 422
