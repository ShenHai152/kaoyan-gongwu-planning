from sqlalchemy import func, select

from app.domains.kaoyan.models import NationalLine
from app.domains.kaoyan.national_line_etl import load_national_lines
from app.domains.kaoyan.national_line_parsing import parse_national_lines
from app.domains.kaoyan.national_line_query import list_national_lines

SAMPLE = {
    "schemaVersion": "1.0.0",
    "retrievedAt": "2026-10-05T13:25:50+08:00",
    "source": {
        "url": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml",
        "publisher": "中国研究生招生信息网（研招网，教育部）",
        "title": "近五年研考分数线及趋势图",
    },
    "unified": [
        {
            "subject": "哲学",
            "totals": {"2022": {"a": 314, "b": 304}, "2026": {"a": 326, "b": 316}},
            "singles": {"2022": {"a1": 45, "a2": 68, "b1": 42, "b2": 63}},
            "evidence": {"sourceUrl": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
        },
        {
            "subject": "交叉学科",
            "totals": {"2023": {"a": 300, "b": 290}},
            "singles": {"2023": {"a1": 40, "a2": 60, "b1": 37, "b2": 56}},
            "evidence": {"sourceUrl": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
        },
    ],
    "separate": [
        {
            "category": "工商管理",
            "totals": {"2022": {"a": 170, "b": 160}},
            "singles": {},
            "evidence": {"sourceUrl": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
        }
    ],
    "specialPrograms": [
        {
            "category": "少数民族骨干计划",
            "totals": {"2022": {"a": 251, "b": 251}},
            "singles": {},
            "evidence": {"sourceUrl": "https://yz.chsi.com.cn/kyzx/zt/lnfsx2026.shtml"},
        }
    ],
}


def test_parses_unified_and_separate_and_special():
    records = parse_national_lines(SAMPLE)
    kinds = {r.category_kind for r in records}
    assert kinds == {"unified", "separate", "special"}
    assert all(r.retrieved_at == "2026-10-05T13:25:50+08:00" for r in records)
    assert all(r.source_url for r in records)


def test_expands_a_and_b_rows():
    records = parse_national_lines(SAMPLE)
    phi = [r for r in records if r.subject == "哲学"]
    assert {r.candidate_type for r in phi} == {"A", "B"}
    a = next(r for r in phi if r.candidate_type == "A")
    assert (a.year, a.total_score) == (2022, 314.0)
    assert (a.single_100, a.single_over100) == (45.0, 68.0)
    b = next(r for r in phi if r.candidate_type == "B")
    assert (b.total_score, b.single_100, b.single_over100) == (304.0, 42.0, 63.0)


def test_all_years_expanded():
    records = parse_national_lines(SAMPLE)
    phi_years = {r.year for r in records if r.subject == "哲学"}
    assert phi_years == {2022, 2026}


def test_load_is_idempotent_and_query(session):
    records = parse_national_lines(SAMPLE)
    load_national_lines(session, records)
    load_national_lines(session, records)
    count = session.scalar(select(func.count()).select_from(NationalLine))
    assert count == len(records)

    result = list_national_lines(session, year=2022, subject="哲学")
    assert {r.candidate_type for r in result} == {"A", "B"}
    assert all(r.category_kind == "unified" for r in result)
