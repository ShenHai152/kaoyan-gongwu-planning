import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.ai.report import build_report
from app.ai.sessions import list_events
from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.ranking import list_program_ranking
from app.llm import FakeProvider
from app.main import app, get_session
from tests.test_kaoyan_ranking import _line


def _seed(factory):
    with factory() as session:
        load_admission_lines(
            session,
            [
                _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, is_985=True),
                _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
                _line(school_name="丙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300, zone="B"),
            ],
        )
        session.commit()


def make_client(engine) -> tuple[TestClient, sessionmaker]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed(factory)
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app), factory


def test_template_report_when_no_provider(engine, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, _ = make_client(engine)
    r = client.post(
        "/api/kaoyan/ai-report",
        json={"score": 350, "program_code": "085404"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["generated_by"] == "template"
    assert body["style"] == "neutral"
    assert body["disclaimer"]
    assert body["summary"]
    assert body["data_refs"]


def test_report_data_refs_match_ranking(engine, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, factory = make_client(engine)
    r = client.post("/api/kaoyan/ai-report", json={"score": 350, "program_code": "085404"})
    body = r.json()
    with factory() as session:
        rows = list_program_ranking(session, year=2026, program_code="085404")
    lines = {row["school_name"]: row["total_score"] for row in rows}
    for ref in body["data_refs"]:
        assert ref["reference_line"] == lines[ref["school"]]


def test_style_switch_same_shape(engine, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, _ = make_client(engine)
    neutral = client.post("/api/kaoyan/ai-report", json={"score": 350, "program_code": "085404"}).json()
    xuefeng = client.post(
        "/api/kaoyan/ai-report",
        json={"score": 350, "program_code": "085404", "style": "xuefeng"},
    ).json()
    assert set(neutral) == set(xuefeng)
    assert xuefeng["style"] == "xuefeng"
    assert neutral["style"] == "neutral"


def test_no_probability_anywhere(engine, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, _ = make_client(engine)
    body = client.post("/api/kaoyan/ai-report", json={"score": 350, "program_code": "085404"}).json()
    blob = json.dumps(body, ensure_ascii=False)
    assert "概率" not in blob or "不预测录取概率" in blob
    assert "录取概率：" not in blob


def test_service_uses_fake_provider_and_records_session(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed(factory)
    with factory() as session:
        provider = FakeProvider(text=json.dumps({"summary": "结论", "sections": []}, ensure_ascii=False))
        report = build_report(
            session,
            score=350,
            program_code="085404",
            program_name=None,
            provider=provider,
        )
        session.commit()
        assert report["generated_by"].startswith("llm:")
        assert report["summary"] == "结论"
        events = list_events(session, report["session_id"])
    kinds = [e.event_type for e in events]
    assert "prompt" in kinds and "input" in kinds and "response" in kinds
    prompt_payload = json.loads(next(e.payload for e in events if e.event_type == "prompt"))
    assert "085404" in prompt_payload["user"]


def test_missing_program_is_422(engine):
    client, _ = make_client(engine)
    r = client.post("/api/kaoyan/ai-report", json={"score": 350})
    assert r.status_code == 422


def test_malformed_model_output_falls_back_to_template(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed(factory)
    with factory() as session:
        provider = FakeProvider(text="not json at all")
        report = build_report(
            session, score=350, program_code="085404", program_name=None, provider=provider
        )
        assert report["generated_by"] == "template"
        assert report["data_refs"]


def test_malformed_sections_are_normalized(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _seed(factory)
    with factory() as session:
        provider = FakeProvider(
            text=json.dumps({"summary": "s", "sections": ["裸字符串", {"title": "t", "points": "bad"}]})
        )
        report = build_report(
            session, score=350, program_code="085404", program_name=None, provider=provider
        )
        assert report["sections"][0] == {"title": "裸字符串", "points": []}
        assert report["sections"][1] == {"title": "t", "points": []}
