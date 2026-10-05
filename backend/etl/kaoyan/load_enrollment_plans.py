"""ETL adapter: raw 招生计划 Excel -> kaoyan EnrollmentPlan records.

2022–2023 files have no year column, so the year is taken from the filename.

Usage:
    python -m etl.kaoyan.load_enrollment_plans [--years 2022 2023 ...]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import python_calamine as pc

from app.db import Base, get_engine, get_sessionmaker
from app.domains.kaoyan.enrollment_etl import load_enrollment_plans
from app.domains.kaoyan.enrollment_parsing import parse_enrollment_rows

RAW_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "rule"
    / "考研招录数据"
    / "历年院校招生计划"
)


def year_from_name(name: str) -> int | None:
    match = re.match(r"\s*(\d{4})", name)
    return int(match.group(1)) if match else None


def find_files(years: list[int] | None) -> list[Path]:
    files = sorted(RAW_DIR.glob("*.xlsx"))
    if not years:
        return files
    return [f for f in files if year_from_name(f.name) in years]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, nargs="*")
    args = parser.parse_args()

    Base.metadata.create_all(get_engine())
    sessionmaker = get_sessionmaker()

    total = 0
    for path in find_files(args.years):
        workbook = pc.load_workbook(str(path))
        sheet = workbook.get_sheet_by_name(workbook.sheet_names[0])
        rows = sheet.to_python()
        records = parse_enrollment_rows(
            rows, source_file=path.name, default_year=year_from_name(path.name)
        )
        with sessionmaker() as session:
            inserted = load_enrollment_plans(session, records)
        total += inserted
        print(f"{path.name}: parsed={len(records)} inserted={inserted}")
    print(f"total inserted: {total}")


if __name__ == "__main__":
    main()
