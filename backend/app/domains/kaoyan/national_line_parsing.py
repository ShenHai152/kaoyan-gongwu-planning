"""Expand the researched national-line JSON into flat NationalLine records.

The research artifact (this project's engineering rules) groups
values by subject/category and year, with A and B candidate types together. This
module flattens one row per (year, kind, subject, candidate_type).
"""

from __future__ import annotations

from dataclasses import dataclass

KIND_BY_GROUP = {
    "unified": "unified",
    "separate": "separate",
    "specialPrograms": "special",
}

_LABEL_KEY = {
    "unified": "subject",
    "separate": "category",
    "specialPrograms": "category",
}


@dataclass(frozen=True)
class NationalLineRecord:
    year: int
    category_kind: str
    subject: str
    candidate_type: str
    total_score: float | None
    single_100: float | None
    single_over100: float | None
    source_url: str
    retrieved_at: str


def _number(value: object) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float, str)):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_national_lines(payload: dict) -> list[NationalLineRecord]:
    source_url = (payload.get("source") or {}).get("url", "")
    retrieved_at = payload.get("retrievedAt", "")
    records: list[NationalLineRecord] = []

    for group, kind in KIND_BY_GROUP.items():
        label_key = _LABEL_KEY[group]
        for item in payload.get(group, []):
            label = item.get(label_key)
            if not label:
                continue
            item_url = (item.get("evidence") or {}).get("sourceUrl", source_url)
            totals = item.get("totals", {})
            singles = item.get("singles", {})
            for year_text, values in totals.items():
                year = int(year_text)
                single = singles.get(year_text, {})
                for candidate_type, key in (("A", "a"), ("B", "b")):
                    total = _number(values.get(key))
                    if total is None:
                        continue
                    records.append(
                        NationalLineRecord(
                            year=year,
                            category_kind=kind,
                            subject=str(label),
                            candidate_type=candidate_type,
                            total_score=total,
                            single_100=_number(single.get(f"{key}1")),
                            single_over100=_number(single.get(f"{key}2")),
                            source_url=item_url or source_url,
                            retrieved_at=retrieved_at,
                        )
                    )
    return records
