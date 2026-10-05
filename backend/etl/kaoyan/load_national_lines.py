"""ETL adapter: researched national-line JSON -> kaoyan NationalLine records.

Source artifact is the verified research output; it is read-only.

Usage:
    python -m etl.kaoyan.load_national_lines [--path <json>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db import Base, get_engine, get_sessionmaker
from app.domains.kaoyan.national_line_etl import load_national_lines
from app.domains.kaoyan.national_line_parsing import parse_national_lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.path.read_text(encoding="utf-8"))
    records = parse_national_lines(payload)

    Base.metadata.create_all(get_engine())
    with get_sessionmaker()() as session:
        inserted = load_national_lines(session, records)
    print(f"{args.path.name}: parsed={len(records)} inserted={inserted}")


if __name__ == "__main__":
    main()
