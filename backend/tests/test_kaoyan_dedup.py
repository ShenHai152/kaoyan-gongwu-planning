from app.domains.kaoyan.parsing import parse_admission_line_rows


def test_duplicate_rows_merge_keeping_real_values(gen1_rows):
    """A placeholder duplicate must not shadow the copy that holds the numbers."""
    header, rows = gen1_rows
    records = parse_admission_line_rows([header, *rows], source_file="2017.xlsx")

    keys = [(r.school_name, r.program_code, r.program_name, r.year) for r in records]
    assert len(records) == 2  # 生药学 + 药物分析学 (two duplicate rows merged)
    assert len(set(keys)) == len(keys)

    merged = next(r for r in records if r.program_name == "药物分析学")
    assert merged.total_score == 300.0
    assert merged.political == 48.0
    assert merged.source_row == 3  # first copy's provenance is retained
