from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.parsing import AdmissionLineRecord
from app.domains.kaoyan.reach_match_safety import (
    MATCH_BAND,
    list_reach_match_safety,
)

BASE = {
    "school_type": None,
    "department": None,
    "degree_type": "专硕",
    "political": None,
    "foreign_language": None,
    "subject_one": None,
    "subject_two": None,
    "total_delta_raw": None,
    "province": "山东",
    "is_985": False,
    "is_211": False,
    "is_double_first_class": False,
    "zone": "A",
    "is_self_drawn": False,
    "website": None,
    "source_file": "t.xlsx",
    "source_row": 1,
}


def _line(**kw):
    return AdmissionLineRecord(**{**BASE, **kw})


def _seed(session, records):
    load_admission_lines(session, records)


def test_bands_by_margin(session):
    # Reference lines 300 / 345 / 360; score 355 gives margins +55 / +10 / -5.
    _seed(
        session,
        [
            _line(school_name="安全大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300),
            _line(school_name="稳妥大学", program_name="计算机技术", program_code="085404", year=2026, total_score=345),
            _line(school_name="冲刺大学", program_name="计算机技术", program_code="085404", year=2026, total_score=360),
        ],
    )
    rows = list_reach_match_safety(
        session, score=355, year_to=2026, window=1, program_code="085404"
    )
    by_school = {r["school_name"]: r for r in rows}
    assert by_school["安全大学"]["band"] == "safety"
    assert by_school["稳妥大学"]["band"] == "match"
    assert by_school["冲刺大学"]["band"] == "reach"
    assert by_school["安全大学"]["margin"] == 55.0
    assert by_school["冲刺大学"]["margin"] == -5.0


def test_threshold_boundaries(session):
    # margins -1 / 0 / MATCH_BAND-1 / MATCH_BAND against a 300 reference.
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=300),
        ],
    )
    assert _band(session, score=299) == "reach"
    assert _band(session, score=300) == "match"
    assert _band(session, score=300 + MATCH_BAND - 1) == "match"
    assert _band(session, score=300 + MATCH_BAND) == "safety"


def _band(session, *, score):
    rows = list_reach_match_safety(
        session, score=score, year_to=2026, window=1, program_code="0001"
    )
    return rows[0]["band"]


def test_reference_line_is_max_over_window(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2024, total_score=350),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2025, total_score=320),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=330),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=3, program_code="0001"
    )
    assert rows[0]["reference_line"] == 350.0
    assert rows[0]["years_observed"] == 3
    assert rows[0]["margin"] == -10.0


def test_window_excludes_older_years(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2022, total_score=400),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=330),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=3, program_code="0001"
    )
    assert rows[0]["reference_line"] == 330.0
    assert rows[0]["years_observed"] == 1


def test_same_school_multiple_departments_take_max(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=320, department="A院"),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=355, department="B院"),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=1, program_code="0001"
    )
    assert len(rows) == 1
    assert rows[0]["reference_line"] == 355.0


def test_single_year_school_still_listed(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=300),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=3, program_code="0001"
    )
    assert rows[0]["years_observed"] == 1


def test_filter_applied_before_banding(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=300, province="北京", is_985=True),
            _line(school_name="乙大学", program_name="X", program_code="0001", year=2026, total_score=300, province="山东", is_985=False),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=1, program_code="0001", is_985=True
    )
    assert [r["school_name"] for r in rows] == ["甲大学"]


def test_sorted_by_margin_ascending(session):
    _seed(
        session,
        [
            _line(school_name="安全大学", program_name="X", program_code="0001", year=2026, total_score=300),
            _line(school_name="冲刺大学", program_name="X", program_code="0001", year=2026, total_score=360),
            _line(school_name="稳妥大学", program_name="X", program_code="0001", year=2026, total_score=340),
        ],
    )
    rows = list_reach_match_safety(
        session, score=350, year_to=2026, window=1, program_code="0001"
    )
    margins = [r["margin"] for r in rows]
    assert margins == sorted(margins)


def test_unknown_program_returns_empty(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=300),
        ],
    )
    assert (
        list_reach_match_safety(
            session, score=340, year_to=2026, window=3, program_code="9999"
        )
        == []
    )


def test_latest_year_reports_newest(session):
    from app.domains.kaoyan.reach_match_safety import latest_year

    assert latest_year(session) is None
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2024, total_score=300),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=330),
        ],
    )
    assert latest_year(session) == 2026


def test_lines_returned_per_year_sorted(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2024, total_score=350),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2025, total_score=320),
            _line(school_name="甲大学", program_name="X", program_code="0001", year=2026, total_score=330),
        ],
    )
    rows = list_reach_match_safety(
        session, score=340, year_to=2026, window=3, program_code="0001"
    )
    assert [ln["year"] for ln in rows[0]["lines"]] == [2024, 2025, 2026]
    assert [ln["total_score"] for ln in rows[0]["lines"]] == [350.0, 320.0, 330.0]


def test_window_must_be_positive(session):
    import pytest

    with pytest.raises(ValueError):
        list_reach_match_safety(
            session, score=340, year_to=2026, window=0, program_code="0001"
        )
