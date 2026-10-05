"""Derive cross-school score rankings from AdmissionLine (GLOSSARY: ScoreRank).

A ranking is a read-time projection, not new authoritative state. Lines are
grouped by school (a school may field several departments for one program), the
highest line stands for the school, and schools are ordered by score descending
with the school name as the stable tie-break. Tied scores share a rank
(standard competition ranking: 1, 2, 2, 4).

A program is identified by its code when given — the code is the cross-year
stable key — otherwise by an exact program name. Both are never ANDed, since a
code and a name may legitimately disagree across years.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import AdmissionLine

DISCLAIMER = (
    "数据来自既有整理资料（非官方），仅作参考；报名决策以当年官方招生简章/"
    "研招网目录/学院公示为准。"
)


@dataclass(frozen=True)
class _Filters:
    year: int
    program_code: str | None = None
    program_name: str | None = None
    zone: str | None = None
    is_985: bool | None = None
    is_211: bool | None = None
    is_self_drawn: bool | None = None


def _school_rows(session: Session, filters: _Filters) -> list[AdmissionLine]:
    if filters.program_code is None and filters.program_name is None:
        raise ValueError("ranking needs a program_code or program_name")

    statement = (
        select(AdmissionLine)
        .where(AdmissionLine.year == filters.year)
        .where(AdmissionLine.total_score.is_not(None))
    )
    if filters.program_code is not None:
        statement = statement.where(AdmissionLine.program_code == filters.program_code)
    elif filters.program_name is not None:
        statement = statement.where(AdmissionLine.program_name == filters.program_name)
    if filters.zone is not None:
        statement = statement.where(AdmissionLine.zone == filters.zone)
    if filters.is_985 is not None:
        statement = statement.where(AdmissionLine.is_985 == filters.is_985)
    if filters.is_211 is not None:
        statement = statement.where(AdmissionLine.is_211 == filters.is_211)
    if filters.is_self_drawn is not None:
        statement = statement.where(
            AdmissionLine.is_self_drawn == filters.is_self_drawn
        )
    return list(session.scalars(statement).all())


def list_program_ranking(
    session: Session,
    *,
    year: int,
    program_code: str | None = None,
    program_name: str | None = None,
    zone: str | None = None,
    is_985: bool | None = None,
    is_211: bool | None = None,
    is_self_drawn: bool | None = None,
) -> list[dict]:
    """Return one row per school, highest line first, with shared ties."""
    lines = _school_rows(
        session,
        _Filters(
            year=year,
            program_code=program_code,
            program_name=program_name,
            zone=zone,
            is_985=is_985,
            is_211=is_211,
            is_self_drawn=is_self_drawn,
        ),
    )

    by_school: dict[str, dict] = {}
    departments: dict[str, set[str]] = {}
    for line in lines:
        entry = by_school.get(line.school_name)
        departments.setdefault(line.school_name, set()).add(line.department or "")
        if entry is None:
            by_school[line.school_name] = {
                "school_name": line.school_name,
                "total_score": line.total_score,
                "political": line.political,
                "foreign_language": line.foreign_language,
                "subject_one": line.subject_one,
                "subject_two": line.subject_two,
                "department": line.department,
                "province": line.province,
                "zone": line.zone,
                "is_985": line.is_985,
                "is_211": line.is_211,
                "is_self_drawn": line.is_self_drawn,
                "source_file": line.source_file,
            }
            continue
        if line.total_score > entry["total_score"]:
            entry["total_score"] = line.total_score
            entry["department"] = line.department
            entry["political"] = line.political
            entry["foreign_language"] = line.foreign_language
            entry["subject_one"] = line.subject_one
            entry["subject_two"] = line.subject_two

    for school_name, entry in by_school.items():
        entry["unit_count"] = len(departments[school_name])

    ordered = sorted(
        by_school.values(),
        key=lambda row: (-row["total_score"], row["school_name"]),
    )
    previous_score: float | None = None
    previous_rank = 0
    for position, row in enumerate(ordered, start=1):
        if row["total_score"] != previous_score:
            previous_rank = position
            previous_score = row["total_score"]
        row["rank"] = previous_rank
    return ordered


def locate_score(rows: list[dict], score: float) -> dict:
    """Where a score would sit in a ranking: insert position and passing count.

    ``schools_passing`` counts schools whose line the score clears
    (score >= line); it is not an admission probability. On an empty ranking
    there is no position, so ``provisional_rank`` is None.
    """
    schools_passing = sum(1 for row in rows if row["total_score"] <= score)
    if not rows:
        provisional_rank = None
    else:
        provisional_rank = 1
        for row in rows:
            if score >= row["total_score"]:
                break
            provisional_rank += 1
    return {
        "score": score,
        "provisional_rank": provisional_rank,
        "schools_passing": schools_passing,
        "total_schools": len(rows),
    }
