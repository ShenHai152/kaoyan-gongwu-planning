"""Read-only reference lookups for form selectors (provinces, programs).

These are projections over AdmissionLine: they own no state and exist so the
frontend never hardcodes a province list or guesses at program codes.
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import AdmissionLine
from app.domains.kaoyan.reach_match_safety import ZONE_MISSING_WARNING

PROGRAMS_DEFAULT_LIMIT = 50
PROGRAMS_MAX_LIMIT = 200


def list_provinces(session: Session) -> list[dict]:
    """Non-empty provinces with their distinct school count, name-ordered."""
    statement = (
        select(
            AdmissionLine.province,
            func.count(func.distinct(AdmissionLine.school_name)),
        )
        .where(AdmissionLine.province.is_not(None))
        .group_by(AdmissionLine.province)
        .order_by(AdmissionLine.province.asc())
    )
    return [
        {"name": province, "school_count": count}
        for province, count in session.execute(statement).all()
    ]


def earliest_province_year(session: Session) -> int | None:
    """First year with any province data; earlier years lack it entirely."""
    value = session.scalar(
        select(func.min(AdmissionLine.year)).where(AdmissionLine.province.is_not(None))
    )
    return int(value) if value is not None else None


def province_coverage_warning(
    session: Session,
    *,
    year_to: int,
    window: int,
    province: str | list[str] | tuple[str, ...] | None,
) -> str | None:
    """Warn when a province filter reaches into years without province data.

    Filtering silently drops the earlier rows, so the result would look smaller
    for a reason the caller cannot see. Return a message instead of nothing.
    """
    if not province:
        return None
    first = earliest_province_year(session)
    if first is None:
        return None
    window_start = year_to - window + 1
    if window_start < first:
        return (
            f"所选窗口含 {window_start}–{first - 1} 年，这些年份缺少省份数据，"
            f"按省份筛选会少算；如需完整覆盖，请把窗口起点设在 {first} 年及以后。"
        )
    return None


def zone_coverage_warning(
    session: Session,
    *,
    year_to: int,
    window: int,
    zone: str | list[str] | tuple[str, ...] | None,
) -> str | None:
    """Warn when a zone filter drops lines that carry no AB-zone value.

    Roughly a quarter of the lines have no zone, and grouping is per school, so
    filtering by AB zone can silently remove schools. Surface the loss instead.
    """
    if not zone:
        return None
    window_start = year_to - window + 1
    missing = session.scalar(
        select(func.count())
        .select_from(AdmissionLine)
        .where(AdmissionLine.year >= window_start)
        .where(AdmissionLine.year <= year_to)
        .where(AdmissionLine.zone.is_(None))
    )
    if not missing:
        return None
    return ZONE_MISSING_WARNING.format(missing=missing)


def search_programs(
    session: Session,
    *,
    query: str | None = None,
    limit: int = PROGRAMS_DEFAULT_LIMIT,
) -> dict:
    """Programs matching a code prefix or a name substring, most schools first.

    A program is (code, name): the code is the cross-year stable key, but 894
    codes carry several names, so both fields are returned. Deterministic order:
    school_count desc, then code asc, then name asc.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    capped = min(limit, PROGRAMS_MAX_LIMIT)

    statement = (
        select(
            AdmissionLine.program_code,
            AdmissionLine.program_name,
            func.count(func.distinct(AdmissionLine.school_name)).label("school_count"),
        )
        .where(AdmissionLine.program_code.is_not(None))
        .group_by(AdmissionLine.program_code, AdmissionLine.program_name)
    )
    if query:
        statement = statement.where(
            or_(
                AdmissionLine.program_code.startswith(query),
                AdmissionLine.program_name.contains(query),
            )
        )
    statement = statement.order_by(
        func.count(func.distinct(AdmissionLine.school_name)).desc(),
        AdmissionLine.program_code.asc(),
        AdmissionLine.program_name.asc(),
    ).limit(capped + 1)

    rows = [
        {
            "program_code": code,
            "program_name": name,
            "school_count": count,
        }
        for code, name, count in session.execute(statement).all()
    ]
    truncated = len(rows) > capped
    return {"rows": rows[:capped], "truncated": truncated, "query": query}
