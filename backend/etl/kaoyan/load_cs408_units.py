"""ETL adapter: vendored kaoyan408 school JSON -> 408 tables.

Source files are read-only third-party data (CC BY 4.0) that is not shipped
with this repository.

Usage:
    python -m etl.kaoyan.load_cs408_units [--dir <schools dir>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_engine
from app.domains.kaoyan.cs408_etl import load_cs408_governance, load_cs408_units
from app.domains.kaoyan.cs408_parsing import (
    parse_conflicts,
    parse_school,
    parse_subject_changes,
)

DEFAULT_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "external"
    / "kaoyan408"
    / "schools"
)


def run(engine: Engine, directory: Path) -> dict[str, int]:
    """Parse every school JSON in ``directory`` into the database.

    A missing or empty directory is a misconfiguration and fails loud instead
    of silently reporting zero.
    """
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no school JSON files under {directory}")

    factory = sessionmaker(bind=engine)
    totals = {"files": 0, "units": 0, "year_lines": 0, "conflicts": 0, "subject_changes": 0}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        units, lines = parse_school(payload, source_file=path.name)
        conflicts = parse_conflicts(payload, source_file=path.name)
        changes = parse_subject_changes(payload, source_file=path.name)
        with factory() as session:
            load_cs408_units(session, units, lines)
            load_cs408_governance(session, conflicts, changes)
        totals["files"] += 1
        totals["units"] += len(units)
        totals["year_lines"] += len(lines)
        totals["conflicts"] += len(conflicts)
        totals["subject_changes"] += len(changes)
    return totals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()

    engine = get_engine()
    Base.metadata.create_all(engine)
    totals = run(engine, args.dir)
    print(
        f"files={totals['files']}, units={totals['units']}, "
        f"year_lines={totals['year_lines']}, conflicts={totals['conflicts']}, "
        f"subject_changes={totals['subject_changes']}"
    )


if __name__ == "__main__":
    main()
