import pytest

from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.reference import (
    earliest_province_year,
    list_provinces,
    province_coverage_warning,
    search_programs,
)
from tests.test_kaoyan_ranking import _line


def _seed(session):
    load_admission_lines(
        session,
        [
            _line(school_name="甲大学", program_name="计算机技术", program_code="085404", year=2026, total_score=370, province="北京"),
            _line(school_name="乙大学", program_name="计算机技术", program_code="085404", year=2026, total_score=340, province="广东"),
            _line(school_name="丙大学", program_name="软件工程", program_code="085405", year=2026, total_score=330, province="北京"),
            _line(school_name="丁大学", program_name="法学", program_code="035101", year=2026, total_score=320, province=None),
        ],
    )


def test_provinces_sorted_with_counts(session):
    _seed(session)
    rows = list_provinces(session)
    assert [r["name"] for r in rows] == ["北京", "广东"]  # None excluded, name order
    assert rows[0] == {"name": "北京", "school_count": 2}
    assert rows[1] == {"name": "广东", "school_count": 1}


def test_provinces_empty_table(session):
    assert list_provinces(session) == []


def test_search_programs_by_code_prefix(session):
    _seed(session)
    result = search_programs(session, query="0854")
    assert [r["program_code"] for r in result["rows"]] == ["085404", "085405"]
    assert result["truncated"] is False


def test_search_programs_by_name_substring(session):
    _seed(session)
    result = search_programs(session, query="计算机")
    assert [r["program_code"] for r in result["rows"]] == ["085404"]


def test_search_programs_limit_and_truncated(session):
    _seed(session)
    result = search_programs(session, query="0854", limit=1)
    assert len(result["rows"]) == 1
    assert result["truncated"] is True


def test_search_programs_empty_query_returns_hot(session):
    _seed(session)
    result = search_programs(session)
    assert result["rows"][0]["program_code"] == "085404"
    assert result["rows"][0]["school_count"] == 2


def test_search_programs_rejects_bad_limit(session):
    with pytest.raises(ValueError):
        search_programs(session, limit=0)


def test_earliest_province_year(session):
    _seed(session)
    assert earliest_province_year(session) == 2026


def test_coverage_warning_fires_when_window_reaches_missing_years(session):
    _seed(session)
    warning = province_coverage_warning(session, year_to=2026, window=8, province="北京")
    assert warning and "少算" in warning


def test_coverage_warning_silent_without_province(session):
    _seed(session)
    assert province_coverage_warning(session, year_to=2026, window=8, province=None) is None


def test_coverage_warning_silent_when_window_is_covered(session):
    _seed(session)
    assert province_coverage_warning(session, year_to=2026, window=1, province="北京") is None
