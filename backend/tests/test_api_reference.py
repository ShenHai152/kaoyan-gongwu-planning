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
                _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, province="北京"),
                _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2020, total_score=340, province=None),
                _line(school_name="丙大学", program_name="软件工程", program_code="085405", year=2026, total_score=330, province="广东"),
            ],
        )
        session.commit()
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app)


def test_provinces_endpoint(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/provinces")
    assert r.status_code == 200
    assert r.json() == [
        {"name": "北京", "school_count": 1},
        {"name": "广东", "school_count": 1},
    ]


def test_programs_endpoint_search(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/programs", params={"query": "0854"})
    body = r.json()
    assert [row["program_code"] for row in body["rows"]] == ["085404", "085405"]
    assert body["truncated"] is False


def test_programs_endpoint_truncated(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/programs", params={"query": "0854", "limit": 1})
    assert r.json()["truncated"] is True


def test_coverage_warning_in_reach_match_safety(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 350, "program_code": "085404", "window": 8, "province": "北京"},
    )
    body = r.json()
    assert body["coverage_warning"] and "少算" in body["coverage_warning"]


def test_coverage_warning_null_when_covered(engine):
    client = make_client(engine)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 350, "program_code": "085404", "window": 1, "province": "北京"},
    )
    assert r.json()["coverage_warning"] is None


def test_reach_match_safety_accepts_repeated_provinces(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        load_admission_lines(
            session,
            [
                _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, province="北京"),
                _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=360, province="广东"),
                _line(school_name="丙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=350, province="上海"),
            ],
        )
        session.commit()
    app.dependency_overrides[get_session] = lambda: factory()
    client = TestClient(app)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params=[
            ("score", 350),
            ("program_code", "085404"),
            ("window", 1),
            ("province", "北京"),
            ("province", "广东"),
        ],
    )
    body = r.json()
    assert r.status_code == 200
    assert {row["province"] for row in body["rows"]} == {"北京", "广东"}


def test_zone_filter_warns_about_missing_zone_data(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        load_admission_lines(
            session,
            [
                _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, zone="A"),
                _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=360, zone=None),
            ],
        )
        session.commit()
    app.dependency_overrides[get_session] = lambda: factory()
    client = TestClient(app)
    r = client.get(
        "/api/kaoyan/reach-match-safety",
        params={"score": 350, "program_code": "085404", "window": 1, "zone": "A"},
    )
    warning = r.json()["coverage_warning"]
    assert warning and "AB 区" in warning
