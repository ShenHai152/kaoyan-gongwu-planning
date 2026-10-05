"""ETL adapter: raw admission-line Excel files -> kaoyan records.

Reads read-only raw Excel files the operator provides, and writes normalized
records to the database. Owns no state (see this project's engineering rules responsibility domains).

Usage:
    python -m etl.kaoyan.load_admission_lines --years 2024 2025 2026
"""

from __future__ import annotations

import argparse
from pathlib import Path

import python_calamine as pc

from app.db import Base, get_engine, get_sessionmaker
from app.domains.kaoyan.etl import load_admission_lines
from app.domains.kaoyan.parsing import parse_admission_line_rows

RAW_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "rule"
    / "考研招录数据"
    / "历年考研复试分数线"
)


def find_files(years: list[int] | None) -> list[Path]:
    files = sorted(RAW_DIR.glob("*.xlsx"))
    if not years:
        return files
    return [f for f in files if any(str(y) in f.name for y in years)]


def read_rows(path: Path) -> list[list]:
    workbook = pc.load_workbook(str(path))
    sheet = workbook.get_sheet_by_name(workbook.sheet_names[0])
    return sheet.to_python()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, nargs="*")
    args = parser.parse_args()

    Base.metadata.create_all(get_engine())
    sessionmaker = get_sessionmaker()

    total = 0
    for path in find_files(args.years):
        rows = read_rows(path)
        records = parse_admission_line_rows(rows, source_file=path.name)
        with sessionmaker() as session:
            inserted = load_admission_lines(session, records)
        total += inserted
        print(f"{path.name}: parsed={len(records)} inserted={inserted}")
    print(f"total inserted: {total}")


if __name__ == "__main__":
    main()
