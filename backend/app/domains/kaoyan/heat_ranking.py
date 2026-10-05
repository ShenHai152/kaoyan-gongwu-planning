"""Derive the 408-track heat ranking from Cs408Unit (GLOSSARY: HeatRank).

The ranking is a read-time projection, not new authoritative state. Heat
signals are upstream third-party scores (`heat_net`, `heat_comp`); units whose
sort key is missing do not participate and are counted instead of silently
placed. Ties share a rank (standard competition ranking: 1, 2, 2, 4), and the
school name is the stable tie-break so the order is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.kaoyan.models import Cs408Unit

DISCLAIMER = (
    "热度为上游第三方整理数据（非官方），仅作参考；不预测录取概率，"
    "报名决策以当年官方招生简章/研招网目录/学院公示为准。"
)

_SORT_FIELDS = {"net": "heat_net", "comp": "heat_comp"}


@dataclass(frozen=True)
class _Filters:
    province: str | None = None
    region: str | None = None
    subject_class: str | None = None
    tier: str | None = None


def _units(session: Session, filters: _Filters) -> list[Cs408Unit]:
    statement = select(Cs408Unit)
    if filters.province is not None:
        statement = statement.where(Cs408Unit.province == filters.province)
    if filters.region is not None:
        statement = statement.where(Cs408Unit.region == filters.region)
    if filters.subject_class is not None:
        statement = statement.where(Cs408Unit.subject_class == filters.subject_class)
    if filters.tier is not None:
        statement = statement.where(Cs408Unit.tier == filters.tier)
    return list(session.scalars(statement).all())


def list_heat_ranking(
    session: Session,
    *,
    sort: str = "net",
    province: str | None = None,
    region: str | None = None,
    subject_class: str | None = None,
    tier: str | None = None,
) -> dict:
    """Return heat-ordered rows with ranks, plus how many lacked the sort key."""
    if sort not in _SORT_FIELDS:
        raise ValueError("sort must be 'net' or 'comp'")
    field = _SORT_FIELDS[sort]

    units = _units(
        session,
        _Filters(
            province=province,
            region=region,
            subject_class=subject_class,
            tier=tier,
        ),
    )

    ranked: list[dict] = []
    excluded_missing = 0
    for unit in units:
        heat = getattr(unit, field)
        if heat is None:
            excluded_missing += 1
            continue
        ranked.append(
            {
                "school_name": unit.school_name,
                "college": unit.college,
                "direction": unit.direction,
                "subject_class": unit.subject_class,
                "province": unit.province,
                "region": unit.region,
                "tier": unit.tier,
                "heat_net": unit.heat_net,
                "heat_comp": unit.heat_comp,
                "wd_count": unit.wd_count,
                "nn_rate_raw": unit.nn_rate_raw,
                "line_2026_value": unit.line_2026_value,
                "admit_cnt_value": unit.admit_cnt_value,
                "src_label": unit.src_label,
                "source_file": unit.source_file,
                "_sort_key": heat,
            }
        )

    ranked.sort(key=lambda row: (-row["_sort_key"], row["school_name"]))

    previous_key: float | None = None
    previous_rank = 0
    for position, row in enumerate(ranked, start=1):
        if row["_sort_key"] != previous_key:
            previous_rank = position
            previous_key = row["_sort_key"]
        row["rank"] = previous_rank
        del row["_sort_key"]

    return {"rows": ranked, "excluded_missing": excluded_missing}
