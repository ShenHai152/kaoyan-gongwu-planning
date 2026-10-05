from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domains.kaoyan.etl import load_admission_lines
from app.main import app, get_session
from tests.test_kaoyan_reach_match_safety import _line


def make_client(engine) -> TestClient:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        load_admission_lines(
            session,
            [
                _line(school_name="安全大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300),
                _line(school_name="稳妥大学", program_name="计算机技术", program_code="085404", year=2026, total_score=345),
                _line(school_name="冲刺大学", program_name="计算机技术", program_code="085404", year=2026, total_score=360),
            ],
        )
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app)


def test_endpoint_bands(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 355, "year_to": 2026, "window": 1, "program_code": "085404"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["disclaimer"]
    bands = {row["school_name"]: row["band"] for row in body["rows"]}
    assert bands == {"安全大学": "safety", "稳妥大学": "match", "冲刺大学": "reach"}
    # rows sorted by margin ascending
    margins = [row["margin"] for row in body["rows"]]
    assert margins == sorted(margins)


def test_endpoint_filter(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={
            "score": 355,
            "year_to": 2026,
            "window": 1,
            "program_code": "085404",
            "province": "北京",
        },
    )
    assert r.status_code == 200
    assert r.json()["rows"] == []


def test_endpoint_requires_program_and_score(engine):
    client = make_client(engine)
    assert (
        client.get(
            "/api/kaoyan/reach-match-safety", params={"year_to": 2026, "score": 355}
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/kaoyan/reach-match-safety",
            params={"year_to": 2026, "program_code": "085404"},
        ).status_code
        == 422
    )


def test_endpoint_empty_is_200(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 355, "year_to": 2026, "program_code": "999999"},
    )
    assert r.status_code == 200
    assert r.json()["rows"] == []


def test_endpoint_defaults_year_to_latest(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 355, "program_code": "085404"},
    )
    assert r.status_code == 200
    assert r.json()["year_to"] == 2026


def test_endpoint_window_zero_is_422(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 355, "year_to": 2026, "window": 0, "program_code": "085404"},
    )
    assert r.status_code == 422


def test_endpoint_empty_database_is_200(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.dependency_overrides[get_session] = lambda: factory()
    client = TestClient(app)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 355, "program_code": "085404"},
    )
    assert r.status_code == 200
    assert r.json()["rows"] == []
    assert r.json()["year_to"] is None
