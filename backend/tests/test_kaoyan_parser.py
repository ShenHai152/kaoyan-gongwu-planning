from app.domains.kaoyan.parsing import parse_admission_line_rows


def test_maps_columns_to_normalized_record(sample_admission_rows):
    header, rows = sample_admission_rows
    records = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")

    assert len(records) == 3
    r = records[0]
    assert r.school_name == "遵义医科大学"
    assert r.program_code == "100208"
    assert r.program_name == "临床检验诊断学"
    assert r.degree_type == "学硕"
    assert r.year == 2026
    assert r.department == "第一临床学院"
    assert r.total_score == 325.0
    assert r.political == 50.0
    assert r.foreign_language == 50.0
    assert r.subject_one == 99.0
    assert r.total_delta_raw == "↑41"
    assert r.school_type == "医药类"
    assert r.province == "贵州"
    assert r.zone == "B"
    assert r.is_self_drawn is False
    assert r.source_file == "2026.xlsx"
    assert r.source_row == 2


def test_bool_flags_and_zone(sample_admission_rows):
    header, rows = sample_admission_rows
    records = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")
    sh = records[1]
    assert sh.is_double_first_class is True
    assert sh.is_985 is False
    assert sh.zone == "A"


def test_record_carries_no_personal_data(sample_admission_rows):
    header, rows = sample_admission_rows
    r = parse_admission_line_rows([header, *rows], source_file="2026.xlsx")[0]
    field_names = " ".join(vars(r).keys())
    assert "姓名" not in field_names
    assert "准考证" not in field_names
    assert "考生" not in field_names
