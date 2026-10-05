from sqlalchemy import func, select

from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.models import AdmissionLine
from app.domains.kaoyan.parsing import parse_admission_line_rows


def test_loads_records(session, sample_admission_rows):
    header, rows = sample_admission_rows
    records = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")
    load_admission_lines(session, records)
    count = session.scalar(select(func.count()).select_from(AdmissionLine))
    assert count == 3


def test_reload_is_idempotent(session, sample_admission_rows):
    header, rows = sample_admission_rows
    records = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")
    load_admission_lines(session, records)
    load_admission_lines(session, records)
    count = session.scalar(select(func.count()).select_from(AdmissionLine))
    assert count == 3
