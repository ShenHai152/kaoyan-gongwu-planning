"""Parse vendored kaoyan408 school JSON into normalized Cs408Unit/YearLine records.

Source: third-party kaoyan408 school JSON (schema `kaoyan-school/v1`,
CC BY 4.0) that is not shipped with this repository. The caliber is a single
college x direction, not the school-wide program, so these records stay
independent from AdmissionLine/EnrollmentPlan.

Values that carry a caliber ("148+1专项", "国家线(264)") keep their original
text; a numeric column is written only when the text parses without ambiguity.
Advisor data (`tutors[]`) is personal data and is never read.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields, replace

_NUMBER = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


@dataclass(frozen=True)
class Cs408UnitRecord:
    school_name: str
    college: str
    direction: str
    category: str | None
    province: str | None
    region: str | None
    tier: str | None
    subject_class: str | None
    line2026_raw: str | None
    line_2026_value: float | None
    line_delta_raw: str | None
    plan2026_raw: str | None
    plan2026_value: float | None
    fill_raw: str | None
    retest_cnt_raw: str | None
    retest_cnt_value: float | None
    admit_cnt_raw: str | None
    admit_cnt_value: float | None
    admit_max_raw: str | None
    admit_max: float | None
    admit_min_raw: str | None
    admit_min: float | None
    admit_avg_raw: str | None
    admit_avg_value: float | None
    heat_net: float | None
    heat_comp: float | None
    nn_408_avg_raw: str | None
    nn_408_avg: float | None
    nn_rate_raw: str | None
    ai_tag: str | None
    scope: str | None
    note: str | None
    src_label: str | None
    kaoqing_url: str | None
    wd_count: float | None
    source_file: str


@dataclass(frozen=True)
class Cs408YearLineRecord:
    school_name: str
    college: str
    direction: str
    year: int
    line_raw: str | None
    line_value: float | None
    source_file: str


def _dumps(value: object) -> str | None:
    if not value:
        return None
    return json.dumps(value, ensure_ascii=False)


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _exact_number(value: object) -> float | None:
    """Return a float only when the whole text is a bare number."""
    text = _text(value)
    if text is None or not _NUMBER.match(text):
        return None
    return float(text)


def _unit_fields(unit: dict) -> dict:
    return {
        "category": _text(unit.get("category")),
        "province": _text(unit.get("province")),
        "region": _text(unit.get("region")),
        "tier": _text(unit.get("tier")),
        "subject_class": _text(unit.get("subjectClass")),
        "line2026_raw": _text(unit.get("line2026")),
        "line_2026_value": _exact_number(unit.get("line2026")),
        "line_delta_raw": _text(unit.get("lineDelta")),
        "plan2026_raw": _text(unit.get("plan2026")),
        "plan2026_value": _exact_number(unit.get("plan2026")),
        "fill_raw": _text(unit.get("fill")),
        "retest_cnt_raw": _text(unit.get("retestCnt")),
        "retest_cnt_value": _exact_number(unit.get("retestCnt")),
        "admit_cnt_raw": _text(unit.get("admitCnt")),
        "admit_cnt_value": _exact_number(unit.get("admitCnt")),
        "admit_max_raw": _text(unit.get("admitMax")),
        "admit_max": _exact_number(unit.get("admitMax")),
        "admit_min_raw": _text(unit.get("admitMin")),
        "admit_min": _exact_number(unit.get("admitMin")),
        "admit_avg_raw": _text(unit.get("admitAvg")),
        "admit_avg_value": _exact_number(unit.get("admitAvg")),
        "heat_net": _exact_number(unit.get("heatNet")),
        "heat_comp": _exact_number(unit.get("heatComp")),
        "nn_408_avg_raw": _text(unit.get("nn408avg")),
        "nn_408_avg": _exact_number(unit.get("nn408avg")),
        "nn_rate_raw": _text(unit.get("nnRate")),
        "ai_tag": _text(unit.get("aiTag")),
        "scope": _text(unit.get("scope")),
        "note": _text(unit.get("note")),
        "src_label": _text(unit.get("srcLabel")),
        "kaoqing_url": _text(unit.get("kaoqingUrl")),
        "wd_count": _exact_number(unit.get("wdCount")),
    }


def _merge_duplicate_units(
    records: list[Cs408UnitRecord],
) -> list[Cs408UnitRecord]:
    merged: dict[tuple, Cs408UnitRecord] = {}
    order: list[tuple] = []
    for record in records:
        key = (record.school_name, record.college, record.direction)
        current = merged.get(key)
        if current is None:
            merged[key] = record
            order.append(key)
            continue
        updates = {
            field.name: getattr(record, field.name)
            for field in fields(record)
            if getattr(current, field.name) is None
            and getattr(record, field.name) is not None
        }
        if updates:
            merged[key] = replace(current, **updates)
    return [merged[key] for key in order]


def parse_school(
    payload: dict, *, source_file: str
) -> tuple[list[Cs408UnitRecord], list[Cs408YearLineRecord]]:
    school_name = _text(payload.get("name"))
    if school_name is None:
        raise ValueError(f"{source_file}: missing required 'name'")
    units: list[Cs408UnitRecord] = []
    lines: list[Cs408YearLineRecord] = []

    for unit in payload.get("units") or []:
        college = _text(unit.get("college"))
        if college is None:
            raise ValueError(f"{source_file}: unit missing required 'college'")
        direction = _text(unit.get("direction")) or ""
        units.append(
            Cs408UnitRecord(
                school_name=school_name,
                college=college,
                direction=direction,
                source_file=source_file,
                **_unit_fields(unit),
            )
        )
        for year_text, value in (unit.get("linesByYear") or {}).items():
            year = int(str(year_text).strip())
            raw = _text(value)
            if raw is None:
                continue
            lines.append(
                Cs408YearLineRecord(
                    school_name=school_name,
                    college=college,
                    direction=direction,
                    year=year,
                    line_raw=raw,
                    line_value=_exact_number(value),
                    source_file=source_file,
                )
            )

    return _merge_duplicate_units(units), lines


@dataclass(frozen=True)
class Cs408ConflictRecord:
    school_name: str
    ordinal: int
    field: str
    unit: str
    old_value: str | None
    new_value: str | None
    reason: str | None
    status: str | None
    action: str | None
    claims_json: str | None
    sources_json: str | None
    source_file: str


@dataclass(frozen=True)
class Cs408SubjectChangeRecord:
    school_name: str
    tier: str | None
    scope: str
    old_subject: str | None
    new_subject: str | None
    effective_year: str | None
    source: str | None
    note: str | None
    source_file: str


def parse_conflicts(payload: dict, *, source_file: str) -> list[Cs408ConflictRecord]:
    school_name = _text(payload.get("name")) or ""
    records: list[Cs408ConflictRecord] = []
    for index, item in enumerate(payload.get("conflicts") or []):
        field = _text(item.get("field")) or ""
        records.append(
            Cs408ConflictRecord(
                school_name=school_name,
                ordinal=index,
                field=field,
                unit=_text(item.get("unit")) or "",
                old_value=_text(item.get("old")),
                new_value=_text(item.get("new")),
                reason=_text(item.get("reason")),
                status=_text(item.get("status")),
                action=_text(item.get("action")),
                claims_json=_dumps(item.get("claims")),
                sources_json=_dumps(item.get("sources")),
                source_file=source_file,
            )
        )
    return records


def parse_subject_changes(
    payload: dict, *, source_file: str
) -> list[Cs408SubjectChangeRecord]:
    school_name = _text(payload.get("name")) or ""
    records: list[Cs408SubjectChangeRecord] = []
    for item in payload.get("updates2027") or []:
        records.append(
            Cs408SubjectChangeRecord(
                school_name=_text(item.get("院校")) or school_name,
                tier=_text(item.get("层次")),
                scope=_text(item.get("专业/范围")) or "",
                old_subject=_text(item.get("原科目")),
                new_subject=_text(item.get("新科目")),
                effective_year=_text(item.get("生效年份")),
                source=_text(item.get("来源")),
                note=_text(item.get("备注")),
                source_file=source_file,
            )
        )
    return records
