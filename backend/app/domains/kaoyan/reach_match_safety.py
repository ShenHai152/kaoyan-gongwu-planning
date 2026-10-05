"""Band candidate schools into reach / match / safety (GLOSSARY: ReachMatchSafety).

A read-time projection over AdmissionLine, not new authoritative state. For one
program, each school's reference line is the highest first-try line inside the
year window; the score margin against that reference decides the band
(GLOSSARY: Band):

    margin = score - reference_line
    margin < 0              → REACH  (冲刺)
    0 <= margin < MATCH_BAND → MATCH  (稳妥)
    margin >= MATCH_BAND     → SAFETY (保底)

The band is about the line only. It is not an admission probability and does not
account for enrollment size or applicant pool.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql.elements import ColumnElement

from app.domains.kaoyan.models import AdmissionLine

MATCH_BAND = 15.0


class Band(StrEnum):
    """Band a school falls into for a given score (GLOSSARY: Band)."""

    REACH = "reach"
    MATCH = "match"
    SAFETY = "safety"


DISCLAIMER = (
    "仅按历年复试线分档，不预测录取概率，也不代表最终录取结果；"
    "报名决策以当年官方招生简章/研招网目录/学院公示为准。"
)

# Distinct admission lines that actually carry a zone (AB 区) value. Roughly a
# quarter of the table lacks it, so a zone filter silently drops those rows;
# expose the count so the UI can warn instead of hiding the loss.
ZONE_MISSING_WARNING = (
    "有 {missing} 条复试线缺少 AB 区信息，按 AB 区筛选会少算；"
    "如需完整覆盖，请不要限定 AB 区。"
)


def latest_year(session: Session) -> int | None:
    """Newest year with any admission line, or None when the table is empty."""
    value = session.scalar(select(func.max(AdmissionLine.year)))
    return int(value) if value is not None else None


@dataclass(frozen=True)
class _Filters:
    year_to: int
    window: int
    score: float
    program_code: str | None = None
    program_name: str | None = None
    province: tuple[str, ...] | None = None
    zone: tuple[str, ...] | None = None
    is_985: bool | None = None
    is_211: bool | None = None
    is_self_drawn: bool | None = None


def _band_for(margin: float) -> Band:
    if margin < 0:
        return Band.REACH
    if margin < MATCH_BAND:
        return Band.MATCH
    return Band.SAFETY


def _as_tuple(
    value: str | list[str] | tuple[str, ...] | None,
) -> tuple[str, ...] | None:
    """Normalize a single value or a repeated query param to a tuple."""
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def _in_filter(
    column: InstrumentedAttribute[str | None], values: tuple[str, ...] | None
) -> ColumnElement[bool] | None:
    return column.in_(values) if values else None


def list_reach_match_safety(
    session: Session,
    *,
    score: float,
    year_to: int,
    window: int,
    program_code: str | None = None,
    program_name: str | None = None,
    province: str | list[str] | tuple[str, ...] | None = None,
    zone: str | list[str] | tuple[str, ...] | None = None,
    is_985: bool | None = None,
    is_211: bool | None = None,
    is_self_drawn: bool | None = None,
) -> list[dict]:
    """One row per school: reference line, margin, band, and its year lines."""
    if program_code is None and program_name is None:
        raise ValueError("reach-match-safety needs a program_code or program_name")
    if window < 1:
        raise ValueError("window must be >= 1")

    provinces = _as_tuple(province)
    zones = _as_tuple(zone)
    filters = _Filters(
        year_to=year_to,
        window=window,
        score=score,
        program_code=program_code,
        program_name=program_name,
        province=provinces,
        zone=zones,
        is_985=is_985,
        is_211=is_211,
        is_self_drawn=is_self_drawn,
    )
    statement = (
        select(AdmissionLine)
        .where(AdmissionLine.year <= filters.year_to)
        .where(AdmissionLine.year > filters.year_to - filters.window)
        .where(AdmissionLine.total_score.is_not(None))
    )
    if filters.program_code is not None:
        statement = statement.where(AdmissionLine.program_code == filters.program_code)
    elif filters.program_name is not None:
        statement = statement.where(AdmissionLine.program_name == filters.program_name)
    province_clause = _in_filter(AdmissionLine.province, filters.province)
    if province_clause is not None:
        statement = statement.where(province_clause)
    zone_clause = _in_filter(AdmissionLine.zone, filters.zone)
    if zone_clause is not None:
        statement = statement.where(zone_clause)
    if filters.is_985 is not None:
        statement = statement.where(AdmissionLine.is_985 == filters.is_985)
    if filters.is_211 is not None:
        statement = statement.where(AdmissionLine.is_211 == filters.is_211)
    if filters.is_self_drawn is not None:
        statement = statement.where(
            AdmissionLine.is_self_drawn == filters.is_self_drawn
        )

    by_school: dict[str, dict] = {}
    lines_by_school: dict[str, dict[int, dict]] = {}
    for line in session.scalars(statement).all():
        year_lines = lines_by_school.setdefault(line.school_name, {})
        existing = year_lines.get(line.year)
        if existing is None or line.total_score > existing["total_score"]:
            year_lines[line.year] = {
                "year": line.year,
                "total_score": line.total_score,
                "department": line.department,
            }
        entry = by_school.get(line.school_name)
        if entry is None:
            by_school[line.school_name] = {
                "school_name": line.school_name,
                "reference_line": line.total_score,
                "department": line.department,
                "province": line.province,
                "zone": line.zone,
                "is_985": line.is_985,
                "is_211": line.is_211,
                "is_self_drawn": line.is_self_drawn,
                "source_file": line.source_file,
            }
            continue
        if line.total_score > entry["reference_line"]:
            entry["reference_line"] = line.total_score
            entry["department"] = line.department

    rows: list[dict] = []
    for school_name, entry in by_school.items():
        margin = filters.score - entry["reference_line"]
        entry["margin"] = margin
        entry["band"] = str(_band_for(margin))
        ordered_lines = sorted(
            lines_by_school[school_name].values(), key=lambda r: r["year"]
        )
        entry["lines"] = ordered_lines
        entry["years_observed"] = len(ordered_lines)
        rows.append(entry)

    rows.sort(key=lambda row: (row["margin"], row["school_name"]))
    return rows
