from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domains.kaoyan.enrollment_etl import load_enrollment_plans
from app.domains.kaoyan.enrollment_parsing import parse_enrollment_rows
from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.national_line_etl import load_national_lines
from app.domains.kaoyan.national_line_parsing import parse_national_lines
from app.domains.kaoyan.parsing import parse_admission_line_rows
from app.main import app, get_session

NATIONAL = {
    "schemaVersion": "1.0.0",
    "retrievedAt": "2026-10-05T13:25:50+08:00",
    "source": {"url": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
    "unified": [
        {
            "subject": "体育学",
            "totals": {"2026": {"a": 310, "b": 300}},
            "singles": {"2026": {"a1": 38, "a2": 114, "b1": 35, "b2": 105}},
            "evidence": {"sourceUrl": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
        }
    ],
}


def make_client(engine, sample_admission_rows, enroll_gen_a_rows) -> TestClient:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        header, rows = sample_admission_rows
        load_admission_lines(
            session,
            parse_admission_line_rows([header, *rows], source_file="2026.xlsx"),
        )
        eheader, erows = enroll_gen_a_rows
        load_enrollment_plans(
            session,
            parse_enrollment_rows(
                [eheader, *erows], source_file="2023.xlsx", default_year=2023
            ),
        )
        load_national_lines(session, parse_national_lines(NATIONAL))

    app.dependency_overrides[get_session] = lambda: factory()
    client = TestClient(app)
    client._factory = factory  # type: ignore[attr-defined]
    return client


def test_admission_lines_endpoint(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get(
        "/api/kaoyan/admission-lines",
        params={"school": "上海体育大学", "program": "体育人文社会学"},
    )
    assert r.status_code == 200
    body = r.json()
    assert [item["year"] for item in body] == [2025, 2026]
    assert body[0]["total_score"] == 295.0


def test_admission_lines_alias(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get(
        "/api/kaoyan/admission-lines",
        params={"school": "上海体育学院", "program": "体育人文社会学"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_admission_lines_empty(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get(
        "/api/kaoyan/admission-lines",
        params={"school": "不存在的大学", "program": "X"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_enrollment_endpoint(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get(
        "/api/kaoyan/enrollment-plans",
        params={"school": "海军军医大学", "program": "内科学"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["enrollment_count"] == 4.0


def test_national_lines_endpoint(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get(
        "/api/kaoyan/national-lines", params={"year": 2026, "subject": "体育学"}
    )
    assert r.status_code == 200
    body = r.json()
    assert {item["candidate_type"] for item in body} == {"A", "B"}
    a = next(item for item in body if item["candidate_type"] == "A")
    assert a["total_score"] == 310.0


def test_national_lines_empty(engine, sample_admission_rows, enroll_gen_a_rows):
    client = make_client(engine, sample_admission_rows, enroll_gen_a_rows)
    r = client.get("/api/kaoyan/national-lines", params={"year": 1999, "subject": "无"})
    assert r.status_code == 200
    assert r.json() == []
