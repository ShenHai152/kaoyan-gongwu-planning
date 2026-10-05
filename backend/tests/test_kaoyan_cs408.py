from pathlib import Path

import pytest

from sqlalchemy import func, select

from app.domains.kaoyan.cs408_etl import load_cs408_governance, load_cs408_units
from app.domains.kaoyan.cs408_parsing import (
    parse_conflicts,
    parse_school,
    parse_subject_changes,
)
from app.domains.kaoyan.models import Cs408Unit, Cs408YearLine

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL = REPO_ROOT / "data" / "external" / "kaoyan408" / "schools" / "001-深圳大学.json"

SAMPLE = {
    "schema": "kaoyan-school/v1",
    "name": "深圳大学",
    "units": [
        {
            "category": "S-主体",
            "province": "广东",
            "region": "华南",
            "tier": "双非",
            "subjectClass": "11408",
            "direction": "不区分研究方向",
            "college": "人工智能学院",
            "line2026": "335",
            "lineDelta": "+71",
            "linesByYear": {
                "2023": None,
                "2024": "324(自命题)",
                "2025": None,
                "2026": "335",
            },
            "fill": "一志愿为主",
            "aiTag": "真AI方向",
            "plan2026": "148+1专项",
            "retestCnt": "34+调剂",
            "admitCnt": "11",
            "admitMax": "423",
            "admitMin": "334",
            "admitAvg": "364",
            "heatNet": "88",
            "heatComp": "65",
            "nn408avg": "101",
            "nnRate": "80%",
            "scope": "085410人工智能(智能系统方向)",
            "srcLabel": "官方",
            "wdCount": "8",
            "kaoqingUrl": "https://noobdream.com/schoolinfo/1/",
        },
        {
            "category": "S-主体",
            "province": "广东",
            "region": "华南",
            "tier": "双非",
            "subjectClass": "11408",
            "direction": None,
            "college": "计算机与软件学院",
            "linesByYear": {"2026": "国家线(264)"},
            "plan2026": "约72(34一志愿+38调剂)",
        },
    ],
    "updates2027": [
        {
            "院校": "深圳大学",
            "层次": "双非",
            "专业/范围": "计院085404",
            "原科目": "数一",
            "新科目": "数二",
            "生效年份": "2027",
            "来源": "官方预公告",
            "备注": "已官宣",
        }
    ],
    "conflicts": [
        {
            "field": "subjectClass",
            "old": "推测22408",
            "new": "11408",
            "reason": "官方目录显示英一数一",
            "sources": ["https://example.com/a"],
        }
    ],
    "tutors": ["张某某（人工智能） 邮箱zhang@example.com"],
    "generated": {"by": "etl_build_db.py", "date": "2026-09-03"},
}


def test_parses_units_and_normalizes_direction():
    units, _ = parse_school(SAMPLE, source_file="001-深圳大学.json")
    assert len(units) == 2
    assert units[0].school_name == "深圳大学"
    assert units[0].college == "人工智能学院"
    assert units[1].direction == ""


def test_text_values_stay_raw_and_no_guessed_number():
    units, _ = parse_school(SAMPLE, source_file="001-深圳大学.json")
    first, second = units
    assert first.plan2026_raw == "148+1专项"
    assert first.plan2026_value is None
    assert first.admit_cnt_value == 11.0
    assert first.admit_cnt_raw == "11"
    assert second.plan2026_value is None
    assert second.plan2026_raw == "约72(34一志愿+38调剂)"


def test_year_lines_expanded_with_raw_and_number():
    _, lines = parse_school(SAMPLE, source_file="001-深圳大学.json")
    keyed = {(ln.college, ln.year): ln for ln in lines}
    assert (("人工智能学院", 2026)) in keyed
    assert keyed[("人工智能学院", 2026)].line_value == 335.0
    assert keyed[("人工智能学院", 2024)].line_value is None
    assert keyed[("人工智能学院", 2024)].line_raw == "324(自命题)"
    assert ("计算机与软件学院", 2026) in keyed
    assert keyed[("计算机与软件学院", 2026)].line_value is None
    assert ("人工智能学院", 2023) not in keyed
    assert ("人工智能学院", 2025) not in keyed


def test_no_tutor_pii_in_records():
    units, lines = parse_school(SAMPLE, source_file="001-深圳大学.json")
    blob = " ".join(str(vars(r)) for r in [*units, *lines])
    assert "张某某" not in blob
    assert "example.com" not in blob
    for record in [*units, *lines]:
        assert not any("tutor" in name or "email" in name for name in vars(record))


def test_load_is_idempotent(session):
    units, lines = parse_school(SAMPLE, source_file="001-深圳大学.json")
    load_cs408_units(session, units, lines)
    load_cs408_units(session, units, lines)
    assert session.scalar(select(func.count()).select_from(Cs408Unit)) == 2
    assert session.scalar(select(func.count()).select_from(Cs408YearLine)) == len(lines)


@pytest.mark.skipif(
    not REAL.exists(), reason="raw kaoyan408 data is not shipped publicly"
)
def test_real_school_file_parses():
    import json

    payload = json.loads(REAL.read_text(encoding="utf-8"))
    units, lines = parse_school(payload, source_file=REAL.name)
    assert units
    assert all(u.school_name == payload["name"] for u in units)
    assert all(u.direction is not None for u in units)
    assert lines


# --- ticket 02: conflicts and 2027 subject changes ---

SAMPLE_CONFLICTS = {
    "name": "测试大学",
    "conflicts": [
        {
            "field": "subjectClass",
            "old": "推测22408",
            "new": "11408",
            "reason": "官方目录显示英一数一",
            "sources": ["https://example.com/a"],
        },
        {
            "field": "计院数学科目",
            "unit": "计算机学院",
            "claims": [
                {"src": "N诺", "value": "数学一"},
                {"src": "王道", "value": "数学二"},
            ],
            "status": "已核实",
            "action": "以官方公告为准",
        },
    ],
}
SAMPLE_CHANGES = {
    "name": "测试大学",
    "updates2027": [
        {
            "院校": "测试大学",
            "层次": "双非",
            "专业/范围": "计院085404",
            "原科目": "数一",
            "新科目": "数二",
            "生效年份": "2027",
            "来源": "官方预公告",
            "备注": "已官宣",
        }
    ],
}


def test_parses_both_conflict_shapes():
    conflicts = parse_conflicts(SAMPLE_CONFLICTS, source_file="x.json")
    assert len(conflicts) == 2
    old_new = next(c for c in conflicts if c.unit == "")
    assert (old_new.old_value, old_new.new_value) == ("推测22408", "11408")
    assert "example.com" in (old_new.sources_json or "")

    claims = next(c for c in conflicts if c.unit == "计算机学院")
    assert claims.status == "已核实"
    assert "数学一" in (claims.claims_json or "")
    assert "数学二" in (claims.claims_json or "")


def test_parses_subject_changes():
    changes = parse_subject_changes(SAMPLE_CHANGES, source_file="x.json")
    assert len(changes) == 1
    change = changes[0]
    assert change.school_name == "测试大学"
    assert change.scope == "计院085404"
    assert (change.old_subject, change.new_subject) == ("数一", "数二")
    assert change.effective_year == "2027"


def test_conflicts_and_changes_load_is_idempotent(session):
    from app.domains.kaoyan.models import Cs408Conflict, Cs408SubjectChange

    conflicts = parse_conflicts(SAMPLE_CONFLICTS, source_file="x.json")
    changes = parse_subject_changes(SAMPLE_CHANGES, source_file="x.json")
    load_cs408_governance(session, conflicts, changes)
    load_cs408_governance(session, conflicts, changes)
    assert session.scalar(select(func.count()).select_from(Cs408Conflict)) == 2
    assert session.scalar(select(func.count()).select_from(Cs408SubjectChange)) == 1


def test_admit_extremes_keep_raw_text():
    payload = {
        "name": "常州大学",
        "units": [
            {
                "college": "计算机学院",
                "direction": "不区分",
                "admitMax": "362(2024)",
                "admitMin": "315(2024)",
                "nn408avg": "113(联培计算机)",
            }
        ],
    }
    units, _ = parse_school(payload, source_file="x.json")
    unit = units[0]
    assert unit.admit_max_raw == "362(2024)"
    assert unit.admit_max is None
    assert unit.admit_min_raw == "315(2024)"
    assert unit.nn_408_avg_raw == "113(联培计算机)"
    assert unit.nn_408_avg is None


def test_missing_name_or_college_fails_loud():
    import pytest

    with pytest.raises(ValueError):
        parse_school({"units": []}, source_file="missing-name.json")
    with pytest.raises(ValueError):
        parse_school(
            {"name": "X", "units": [{"direction": "不区分"}]},
            source_file="missing-college.json",
        )


def test_empty_units_is_noop(session):
    from app.domains.kaoyan.models import Cs408Conflict

    units, lines = parse_school({"name": "空大学", "units": []}, source_file="x.json")
    assert units == [] and lines == []
    assert load_cs408_units(session, units, lines) == 0
    assert session.scalar(select(func.count()).select_from(Cs408Unit)) == 0
    assert session.scalar(select(func.count()).select_from(Cs408Conflict)) == 0


def test_year_line_by_year_filter(session):
    from app.domains.kaoyan.cs408_query import list_cs408_year_lines

    units, lines = parse_school(SAMPLE, source_file="001-深圳大学.json")
    load_cs408_units(session, units, lines)
    rows = list_cs408_year_lines(session, school="深圳大学", year=2026)
    assert {r["college"] for r in rows} == {"人工智能学院", "计算机与软件学院"}
    assert all(r["year"] == 2026 for r in rows)


def test_year_line_requires_owning_unit(session):
    from app.domains.kaoyan.models import Cs408YearLine

    units, _ = parse_school(SAMPLE, source_file="001-深圳大学.json")
    load_cs408_units(session, units, [])
    orphan = Cs408YearLine(unit_id=9999, year=2026, line_raw="300", source_file="x")
    session.add(orphan)
    import pytest
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        session.commit()
