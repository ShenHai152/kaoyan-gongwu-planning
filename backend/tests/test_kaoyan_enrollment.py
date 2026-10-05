from sqlalchemy import func, select

from app.domains.kaoyan.enrollment_etl import load_enrollment_plans
from app.domains.kaoyan.enrollment_parsing import parse_enrollment_rows
from app.domains.kaoyan.enrollment_query import list_enrollment_plans
from app.domains.kaoyan.models import EnrollmentPlan


def test_parses_generation_a(enroll_gen_a_rows):
    header, rows = enroll_gen_a_rows
    records = parse_enrollment_rows(
        [header, *rows], source_file="2023.xlsx", default_year=2023
    )
    first = records[0]
    assert first.school_name == "海军军医大学"
    assert first.program_code == "105101"
    assert first.program_name == "内科学"
    assert first.degree_type == "专硕"
    assert first.study_mode == "全日制"
    assert first.enrollment_count == 4
    assert first.enrollment_raw == "专业：4(不含推免)"
    assert "某某" not in (first.direction or "")
    assert first.exam_subjects is not None and "思想政治理论" in first.exam_subjects
    assert first.is_double_first_class is True
    assert first.year == 2023


def test_parses_generation_b(enroll_gen_b_rows):
    header, rows = enroll_gen_b_rows
    record = parse_enrollment_rows([header, *rows], source_file="2026.xlsx")[0]
    assert record.school_name == "湖北大学"
    assert record.program_code == "010100"
    assert record.degree_type == "学硕"
    assert record.enrollment_count == 46
    assert record.zone == "A"
    assert record.direction == "（04）逻辑学"


def test_no_advisor_field_in_records(enroll_gen_a_rows):
    header, rows = enroll_gen_a_rows
    record = parse_enrollment_rows([header, *rows], source_file="2023.xlsx")[0]
    field_names = " ".join(vars(record).keys())
    assert "指导" not in field_names
    assert "导师" not in field_names
    assert "姓名" not in field_names


def test_load_and_query(session, enroll_gen_a_rows):
    header, rows = enroll_gen_a_rows
    records = parse_enrollment_rows([header, *rows], source_file="2023.xlsx")
    load_enrollment_plans(session, records)
    load_enrollment_plans(session, records)  # idempotent
    count = session.scalar(select(func.count()).select_from(EnrollmentPlan))
    assert count == 2

    result = list_enrollment_plans(session, school="海军军医大学", program="内科学")
    assert len(result) == 1
    assert result[0].enrollment_count == 4
