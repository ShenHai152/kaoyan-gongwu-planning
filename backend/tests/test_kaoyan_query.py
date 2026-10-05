from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.parsing import parse_admission_line_rows
from app.domains.kaoyan.query import list_admission_lines


def _seed(session, sample_admission_rows):
    header, rows = sample_admission_rows
    records = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")
    load_admission_lines(session, records)


def test_returns_lines_sorted_by_year(session, sample_admission_rows):
    _seed(session, sample_admission_rows)
    result = list_admission_lines(
        session, school="上海体育大学", program="体育人文社会学"
    )
    assert [r.year for r in result] == [2025, 2026]
    assert result[0].total_score == 295.0


def test_matches_school_alias(session, sample_admission_rows):
    _seed(session, sample_admission_rows)
    result = list_admission_lines(
        session, school="上海体育学院", program="体育人文社会学"
    )
    assert len(result) == 2


def test_missing_program_returns_empty(session, sample_admission_rows):
    _seed(session, sample_admission_rows)
    assert (
        list_admission_lines(session, school="上海体育大学", program="不存在专业") == []
    )
