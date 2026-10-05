from sqlalchemy import func, select

from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.models import AdmissionLine
from app.domains.kaoyan.parsing import (
    detect_generation,
    parse_admission_line_rows,
)
from app.domains.kaoyan.query import list_admission_lines


def test_detect_generation(gen1_rows, gen2_rows, sample_admission_rows):
    gen1_header, _ = gen1_rows
    gen2_header, _ = gen2_rows
    gen3_header, _ = sample_admission_rows
    assert detect_generation(gen1_header) == 1
    assert detect_generation(gen2_header) == 2
    assert detect_generation(gen3_header) == 3


def test_parses_generation_1(gen1_rows):
    header, rows = gen1_rows
    records = parse_admission_line_rows([header, *rows], source_file="2017.xlsx")
    record = records[0]
    assert record.school_name == "兰州大学"
    assert record.department == "药学院"
    assert record.program_name == "生药学"
    assert record.year == 2017
    assert record.total_score == 295.0
    assert record.political == 50.0
    assert record.subject_two is None  # "-" is a placeholder
    assert record.total_delta_raw is None
    assert record.is_985 is False


def test_parses_generation_2_and_derives_attributes(gen2_rows):
    header, rows = gen2_rows
    records = parse_admission_line_rows([header, *rows], source_file="2020.xlsx")
    first = records[0]
    assert first.school_name == "武汉大学"
    assert first.degree_type == "专硕"
    assert first.school_type == "综合类"
    assert first.is_985 is True
    assert first.is_211 is True
    assert first.is_double_first_class is True
    assert first.is_self_drawn is True
    assert first.zone == "A"
    assert first.department is None
    assert records[1].degree_type == "学硕"
    assert records[1].is_self_drawn is False


def test_cross_generation_query_sorted(session, gen2_rows, sample_admission_rows):
    header2, rows2 = gen2_rows
    header3, rows3 = sample_admission_rows
    load_admission_lines(
        session, parse_admission_line_rows([header3, *rows3], source_file="2026.xlsx")
    )
    load_admission_lines(
        session, parse_admission_line_rows([header2, *rows2], source_file="2020.xlsx")
    )
    result = list_admission_lines(
        session, school="上海体育大学", program="体育人文社会学"
    )
    assert [r.year for r in result] == [2025, 2026]
    wu = list_admission_lines(session, school="武汉大学", program="工程管理")
    assert [r.year for r in wu] == [2020]
    assert wu[0].is_985 is True


def test_mixed_reload_is_idempotent(
    session, gen1_rows, gen2_rows, sample_admission_rows
):
    header1, rows1 = gen1_rows
    header2, rows2 = gen2_rows
    header3, rows3 = sample_admission_rows
    records = (
        parse_admission_line_rows([header1, *rows1], source_file="2017.xlsx")
        + parse_admission_line_rows([header2, *rows2], source_file="2020.xlsx")
        + parse_admission_line_rows([header3, *rows3], source_file="2026.xlsx")
    )
    load_admission_lines(session, records)
    load_admission_lines(session, records)
    count = session.scalar(select(func.count()).select_from(AdmissionLine))
    assert count == 7
