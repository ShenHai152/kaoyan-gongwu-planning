"""Parse raw 复试分数线 rows into normalized admission-line records.

The parser is header-adaptive: it maps whatever columns a file has (using
aliases) rather than assuming fixed positions, so three generations normalize
to the same record:

- 2017–2019: 13 columns (学校名称/院系名称/业务课_一)
- 2020–2023: 23 columns (学校/硕士类型/学校属性)
- 2024–2026: 29 columns (院校名称/专硕学硕/985…自划线/AB区)

Values missing in an older generation are left empty; a packed 学校属性 string
is expanded into the boolean/zone fields. See
this project's engineering rules
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, replace

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "year": ("年份",),
    "school_name": ("院校名称", "学校名称", "学校"),
    "school_type": ("院校类型",),
    "program_name": ("专业名称",),
    "program_code": ("专业代码",),
    "department": ("所属院系", "院系名称", "院系所"),
    "degree_type": ("专硕/学硕", "硕士类型"),
    "total_score": ("总分",),
    "total_delta_raw": ("总分线差",),
    "political": ("政治", "政治__管综"),
    "foreign_language": ("外语", "英语"),
    "subject_one": ("专业课一", "业务课一", "业务课_一"),
    "subject_two": ("专业课二", "业务课二", "业务课_二"),
    "province": ("所在地", "学校省份"),
    "is_985": ("985",),
    "is_211": ("211",),
    "is_double_first_class": ("双一流",),
    "zone": ("AB区",),
    "is_self_drawn": ("自划线",),
    "website": ("招生官网", "学校官网"),
    "school_attr": ("学校属性",),
}

_SCHOOL_TYPES = frozenset(
    {
        "综合类",
        "医药类",
        "理工类",
        "师范类",
        "农林类",
        "财经类",
        "政法类",
        "语言类",
        "艺术类",
        "体育类",
        "民族类",
        "军事类",
    }
)

_DEGREE_TYPE_MAP = {
    "专业型硕士": "专硕",
    "学术型硕士": "学硕",
    "专业学位": "专硕",
    "学术学位": "学硕",
}


def detect_generation(header: list) -> int:
    """Return 1, 2, or 3 for the 13/23/29-column generations."""
    columns = {str(cell).strip() for cell in header}
    if "专硕/学硕" in columns and "总分线差" in columns:
        return 3
    if "硕士类型" in columns and "学校属性" in columns:
        return 2
    if "学校名称" in columns and "业务课_一" in columns:
        return 1
    return 0


def _attribute_fields(attr: str | None) -> dict:
    """Expand a packed 学校属性 string into flags, zone, and school type."""
    if not attr:
        return {}
    tokens = [token for token in re.split(r"\s+", attr.strip()) if token]
    return {
        "is_985": "985" in tokens,
        "is_211": "211" in tokens,
        "is_double_first_class": "双一流" in tokens,
        "is_self_drawn": "自划线" in tokens,
        "zone": next((t[0] for t in tokens if t in ("A区", "B区")), None),
        "school_type": next((t for t in tokens if t in _SCHOOL_TYPES), None),
    }


def _degree_type(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return _DEGREE_TYPE_MAP.get(text, text)


@dataclass(frozen=True)
class AdmissionLineRecord:
    school_name: str
    school_type: str | None
    program_name: str
    program_code: str | None
    department: str | None
    degree_type: str | None
    year: int
    total_score: float | None
    political: float | None
    foreign_language: float | None
    subject_one: float | None
    subject_two: float | None
    total_delta_raw: str | None
    province: str | None
    is_985: bool
    is_211: bool
    is_double_first_class: bool
    zone: str | None
    is_self_drawn: bool
    website: str | None
    source_file: str
    source_row: int


def _build_index(header: list[str]) -> dict[str, int]:
    normalized = {str(cell).strip(): i for i, cell in enumerate(header)}
    index: dict[str, int] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                index[field] = normalized[alias]
                break
    return index


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: object) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _year(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _flag(value: object) -> bool:
    text = _text(value)
    return text is not None and text not in {"否", "0", "无", "-", ""}


def _cell(row: list, index: dict[str, int], field: str) -> object:
    position = index.get(field)
    if position is None or position >= len(row):
        return None
    return row[position]


def _flag_from_column_or_attr(
    row: list, index: dict[str, int], field: str, attr: dict
) -> bool:
    if field in index:
        return _flag(_cell(row, index, field))
    return bool(attr.get(field, False))


_MERGE_KEY = (
    "school_name",
    "program_code",
    "program_name",
    "degree_type",
    "year",
    "department",
)


def _merge_duplicate_records(
    records: list[AdmissionLineRecord],
) -> list[AdmissionLineRecord]:
    """Collapse rows sharing a business key, keeping the first and filling gaps.

    Older raw files repeat a logical line once per source URL, and the first
    copy sometimes carries only placeholders while a later copy holds the real
    numbers. Merging by first-non-null recovers those values instead of losing
    them to deduplication.
    """
    merged: dict[tuple, AdmissionLineRecord] = {}
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


def parse_admission_line_rows(
    rows: list[list], source_file: str
) -> list[AdmissionLineRecord]:
    if not rows:
        return []
    index = _build_index(list(rows[0]))
    generation = detect_generation(list(rows[0]))
    records: list[AdmissionLineRecord] = []
    for offset, row in enumerate(rows[1:], start=2):
        school = _text(_cell(row, index, "school_name"))
        program = _text(_cell(row, index, "program_name"))
        year = _year(_cell(row, index, "year"))
        if not school or not program or year is None:
            continue
        attr = (
            _attribute_fields(_text(_cell(row, index, "school_attr")))
            if generation == 2
            else {}
        )

        school_type = _text(_cell(row, index, "school_type")) or attr.get("school_type")
        zone = _text(_cell(row, index, "zone")) or attr.get("zone")
        records.append(
            AdmissionLineRecord(
                school_name=school,
                school_type=school_type,
                program_name=program,
                program_code=_text(_cell(row, index, "program_code")),
                department=_text(_cell(row, index, "department")),
                degree_type=_degree_type(_cell(row, index, "degree_type")),
                year=year,
                total_score=_number(_cell(row, index, "total_score")),
                political=_number(_cell(row, index, "political")),
                foreign_language=_number(_cell(row, index, "foreign_language")),
                subject_one=_number(_cell(row, index, "subject_one")),
                subject_two=_number(_cell(row, index, "subject_two")),
                total_delta_raw=_text(_cell(row, index, "total_delta_raw")),
                province=_text(_cell(row, index, "province")),
                is_985=_flag_from_column_or_attr(row, index, "is_985", attr),
                is_211=_flag_from_column_or_attr(row, index, "is_211", attr),
                is_double_first_class=_flag_from_column_or_attr(
                    row, index, "is_double_first_class", attr
                ),
                zone=zone,
                is_self_drawn=_flag_from_column_or_attr(
                    row, index, "is_self_drawn", attr
                ),
                website=_text(_cell(row, index, "website")),
                source_file=source_file,
                source_row=offset,
            )
        )
    return _merge_duplicate_records(records)
