"""Parse raw 招生计划 rows into normalized EnrollmentPlan records.

Two generations normalize to one record:

- 2022–2023 (16 cols): 院校名称/(专业)/(学习方式)/(研究方向)/(拟招人数)...
- 2024–2026 (27–29 cols): 院校名称/专业名称/专业代码/学习方式/招生人数...

Advisor names (`指导老师`, and any advisor suffix embedded in `研究方向`) are
personal data and are dropped — never stored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, replace

from app.domains.kaoyan.parsing import (
    _attribute_fields,
    _cell,
    _degree_type,
    _flag_from_column_or_attr,
    _number,
    _text,
)

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "year": ("年份",),
    "school_name": ("院校名称", "学校名称", "学校"),
    "school_code": ("院校代码",),
    "school_tier": ("院校层级",),
    "program_name": ("专业名称", "专业"),
    "program_code": ("专业代码",),
    "department": ("所属院系", "院系所"),
    "degree_type": ("专硕/学硕", "硕士类型"),
    "study_mode": ("学习方式",),
    "direction": ("研究方向",),
    "enrollment": ("招生人数", "拟招人数"),
    "enrollment_note": ("招生人数说明", "备注"),
    "exam_method": ("考试方式",),
    "exam_subjects": ("考试科目",),
    "political": ("政治", "政治综合"),
    "foreign_language": ("外语",),
    "subject_one": ("业务课一",),
    "subject_two": ("业务课二",),
    "city": ("所在城市",),
    "province": ("所在地",),
    "website": ("招生官网",),
    "school_attr": ("学校属性",),
    "is_985": ("985",),
    "is_211": ("211",),
    "is_double_first_class": ("双一流",),
    "zone": ("AB区",),
    "is_self_drawn": ("自划线",),
}


@dataclass(frozen=True)
class EnrollmentPlanRecord:
    school_name: str
    school_code: str | None
    program_name: str
    program_code: str | None
    department: str | None
    degree_type: str | None
    study_mode: str | None
    direction: str | None
    year: int
    enrollment_count: float | None
    enrollment_raw: str | None
    enrollment_note: str | None
    exam_method: str | None
    exam_subjects: str | None
    city: str | None
    province: str | None
    is_985: bool
    is_211: bool
    is_double_first_class: bool
    zone: str | None
    is_self_drawn: bool
    source_file: str
    source_row: int


def detect_generation(header: list) -> str:
    columns = {str(cell).strip() for cell in header}
    if "招生人数" in columns:
        return "B"
    if "拟招人数" in columns:
        return "A"
    return ""


def _build_index(header: list) -> dict[str, int]:
    normalized = {str(cell).strip(): i for i, cell in enumerate(header)}
    index: dict[str, int] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                index[field] = normalized[alias]
                break
    return index


def _strip_advisor(text: str | None) -> str | None:
    if text is None:
        return None
    # A leading "（NN）" direction code is kept; a trailing "-姓名" suffix is not.
    cleaned = re.sub(r"-\s*[^-]{2,10}$", "", text).strip()
    cleaned = re.sub(r"\s{2,}.*$", "", cleaned).strip()
    return cleaned or None


def _program(code_text: str | None, name_text: str | None) -> tuple[str | None, str]:
    code = code_text
    name = name_text or ""
    match = re.match(r"^\((\d+)\)(.*)$", name)
    if match:
        if code is None:
            code = match.group(1)
        name = match.group(2)
    name = re.sub(r"^\([^)]*学位\)|^（[^）]*学位）", "", name).strip()
    return code, name.strip()


def _degree_from_program(raw: str | None) -> str | None:
    if not raw:
        return None
    if "专业学位" in raw or "专业型" in raw:
        return "专硕"
    if "学术学位" in raw or "学术型" in raw:
        return "学硕"
    return None


def _enrollment(value: object) -> tuple[float | None, str | None]:
    text = _text(value)
    if text is None:
        return None, None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return (float(match.group(1)) if match else None), text


def _join_subjects(row: list, index: dict[str, int]) -> str | None:
    if "exam_subjects" in index:
        return _text(_cell(row, index, "exam_subjects"))
    parts = [
        _text(_cell(row, index, field))
        for field in ("political", "foreign_language", "subject_one", "subject_two")
    ]
    joined = " / ".join(part for part in parts if part)
    return joined or None


def parse_enrollment_rows(
    rows: list[list], source_file: str, default_year: int | None = None
) -> list[EnrollmentPlanRecord]:
    if not rows:
        return []
    header = list(rows[0])
    index = _build_index(header)
    generation = detect_generation(header)
    current_year: int | None = None
    records: list[EnrollmentPlanRecord] = []

    for offset, row in enumerate(rows[1:], start=2):
        school = _text(_cell(row, index, "school_name"))
        if school is None:
            continue
        year = _number(_cell(row, index, "year"))
        if year is not None:
            current_year = int(year)
        if generation == "A" and current_year is None:
            current_year = default_year

        code, name = _program(
            _text(_cell(row, index, "program_code")),
            _text(_cell(row, index, "program_name")),
        )
        if not name:
            continue
        degree = _degree_type(_text(_cell(row, index, "degree_type"))) or (
            _degree_from_program(_text(_cell(row, index, "program_name")))
        )
        attr = (
            _attribute_fields(_text(_cell(row, index, "school_attr")))
            if "school_attr" in index
            else {}
        )
        tier = _text(_cell(row, index, "school_tier"))
        if tier and "双一流" in tier:
            attr.setdefault("is_double_first_class", True)
        count, raw = _enrollment(_cell(row, index, "enrollment"))
        records.append(
            EnrollmentPlanRecord(
                school_name=school,
                school_code=_text(_cell(row, index, "school_code")),
                program_name=name,
                program_code=code,
                department=_text(_cell(row, index, "department")),
                degree_type=degree,
                study_mode=_text(_cell(row, index, "study_mode")),
                direction=_strip_advisor(_text(_cell(row, index, "direction"))),
                year=current_year or 0,
                enrollment_count=count,
                enrollment_raw=raw,
                enrollment_note=_text(_cell(row, index, "enrollment_note")),
                exam_method=_text(_cell(row, index, "exam_method")),
                exam_subjects=_join_subjects(row, index),
                city=_text(_cell(row, index, "city")),
                province=_text(_cell(row, index, "province")),
                is_985=_flag_from_column_or_attr(row, index, "is_985", attr),
                is_211=_flag_from_column_or_attr(row, index, "is_211", attr),
                is_double_first_class=_flag_from_column_or_attr(
                    row, index, "is_double_first_class", attr
                ),
                zone=_text(_cell(row, index, "zone")) or attr.get("zone"),
                is_self_drawn=_flag_from_column_or_attr(
                    row, index, "is_self_drawn", attr
                ),
                source_file=source_file,
                source_row=offset,
            )
        )
    return _merge(records)


_MERGE_KEY = ("school_name", "program_name", "study_mode", "direction", "year")


def _merge(records: list[EnrollmentPlanRecord]) -> list[EnrollmentPlanRecord]:
    merged: dict[tuple, EnrollmentPlanRecord] = {}
    order: list[tuple] = []
    for record in records:
        key = tuple(getattr(record, field) for field in _MERGE_KEY)
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
