from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.parsing import AdmissionLineRecord
from app.domains.kaoyan.ranking import list_program_ranking

BASE = {
    "school_type": None,
    "department": None,
    "degree_type": "专硕",
    "political": None,
    "foreign_language": None,
    "subject_one": None,
    "subject_two": None,
    "total_delta_raw": None,
    "province": None,
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


def test_ranks_by_score_descending(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
            _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370),
            _line(school_name="丙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300),
        ],
    )
    rows = list_program_ranking(session, year=2026, program_code="085404")
    assert [(r["school_name"], r["rank"]) for r in rows] == [
        ("乙大学", 1),
        ("甲大学", 2),
        ("丙大学", 3),
    ]


def test_ties_share_rank_and_sort_by_codepoint(session):
    # Inserted out of name order; the tie-break is the school name's code-point
    # order (deterministic and reproducible), not pinyin.
    _seed(
        session,
        [
            _line(school_name="B大学", program_name="会计", program_code="1253", year=2026, total_score=350),
            _line(school_name="A大学", program_name="会计", program_code="1253", year=2026, total_score=350),
            _line(school_name="C大学", program_name="会计", program_code="1253", year=2026, total_score=340),
        ],
    )
    rows = list_program_ranking(session, year=2026, program_code="1253")
    assert [r["rank"] for r in rows] == [1, 1, 3]
    assert [r["school_name"] for r in rows] == ["A大学", "B大学", "C大学"]


def test_same_school_keeps_highest_line_and_counts_departments(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="电子信息", program_code="0854", year=2026, total_score=300, department="A院"),
            _line(school_name="甲大学", program_name="电子信息", program_code="0854", year=2026, total_score=330, department="B院"),
            _line(school_name="甲大学", program_name="电子信息", program_code="0854", year=2026, total_score=325, department="B院"),
            _line(school_name="乙大学", program_name="电子信息", program_code="0854", year=2026, total_score=310, department="C院"),
        ],
    )
    rows = list_program_ranking(session, year=2026, program_code="0854")
    # unit_count is distinct departments, so 甲大学's two B院 rows count once.
    assert [(r["school_name"], r["total_score"], r["unit_count"]) for r in rows] == [
        ("甲大学", 330.0, 2),
        ("乙大学", 310.0, 1),
    ]


def test_program_code_takes_priority_over_name(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
            _line(school_name="乙大学", program_name="旧名计算机", program_code="085404", year=2025, total_score=330),
        ],
    )
    # Code wins even when the name disagrees (e.g. a renamed program).
    rows = list_program_ranking(
        session, year=2026, program_code="085404", program_name="计算机技术"
    )
    assert [r["school_name"] for r in rows] == ["甲大学"]


def test_filters_by_zone_and_985(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340, zone="A", is_985=True),
            _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300, zone="B", is_985=False),
        ],
    )
    a_zone = list_program_ranking(session, year=2026, program_code="085404", zone="A")
    assert [r["school_name"] for r in a_zone] == ["甲大学"]
    only_985 = list_program_ranking(session, year=2026, program_code="085404", is_985=True)
    assert [r["school_name"] for r in only_985] == ["甲大学"]


def test_unknown_program_returns_empty(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
        ],
    )
    assert list_program_ranking(session, year=2026, program_code="999999") == []
    assert list_program_ranking(session, year=1999, program_code="085404") == []


def test_requires_program_identifier(session):
    import pytest

    with pytest.raises(ValueError):
        list_program_ranking(session, year=2026)


def test_rows_without_score_are_excluded(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=None),
            _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300),
        ],
    )
    rows = list_program_ranking(session, year=2026, program_code="085404")
    assert [r["school_name"] for r in rows] == ["乙大学"]


# --- ticket 02: score positioning ---

from app.domains.kaoyan.ranking import locate_score


def _ranking(session):
    _seed(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370),
            _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340),
            _line(school_name="丙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=300),
        ],
    )
    return list_program_ranking(session, year=2026, program_code="085404")


def test_score_above_top(session):
    result = locate_score(_ranking(session), 400)
    assert result["provisional_rank"] == 1
    assert result["schools_passing"] == 3
    assert result["total_schools"] == 3


def test_score_equal_to_a_line(session):
    result = locate_score(_ranking(session), 340)
    assert result["provisional_rank"] == 2
    assert result["schools_passing"] == 2


def test_score_between_lines(session):
    result = locate_score(_ranking(session), 350)
    assert result["provisional_rank"] == 2
    assert result["schools_passing"] == 2


def test_score_below_bottom(session):
    result = locate_score(_ranking(session), 200)
    assert result["provisional_rank"] == 4
    assert result["schools_passing"] == 0


def test_score_on_empty_ranking_has_no_rank(session):
    result = locate_score([], 300)
    assert result["provisional_rank"] is None
    assert result["schools_passing"] == 0
    assert result["total_schools"] == 0
