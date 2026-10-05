"""Response models for the kaoyan read API (single source of the contract)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AdmissionLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    school_name: str
    program_name: str
    program_code: str | None
    department: str | None
    degree_type: str | None
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


class EnrollmentPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    school_name: str
    program_name: str
    program_code: str | None
    department: str | None
    degree_type: str | None
    study_mode: str | None
    direction: str | None
    enrollment_count: float | None
    enrollment_raw: str | None
    enrollment_note: str | None
    exam_method: str | None
    exam_subjects: str | None
    city: str | None
    province: str | None
    zone: str | None
    source_file: str


class NationalLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    category_kind: str
    subject: str
    candidate_type: str
    total_score: float | None
    single_100: float | None
    single_over100: float | None
    source_url: str
    retrieved_at: str


class Cs408UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class Cs408YearLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_name: str
    college: str
    direction: str
    year: int
    line_raw: str | None
    line_value: float | None
    source_file: str


class Cs408SubjectChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_name: str
    tier: str | None
    scope: str
    old_subject: str | None
    new_subject: str | None
    effective_year: str | None
    source: str | None
    note: str | None
    source_file: str


class Cs408ConflictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_name: str
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


class RankingRowOut(BaseModel):
    school_name: str
    rank: int
    total_score: float
    political: float | None
    foreign_language: float | None
    subject_one: float | None
    subject_two: float | None
    unit_count: int
    department: str | None
    province: str | None
    zone: str | None
    is_985: bool
    is_211: bool
    is_self_drawn: bool
    source_file: str


class ScorePositionOut(BaseModel):
    score: float
    provisional_rank: int | None
    schools_passing: int
    total_schools: int


class ProgramRankingOut(BaseModel):
    year: int
    program_code: str | None
    program_name: str | None
    disclaimer: str
    rows: list[RankingRowOut]
    position: ScorePositionOut | None


class ReachMatchSafetyYearLineOut(BaseModel):
    year: int
    total_score: float
    department: str | None


class ReachMatchSafetyRowOut(BaseModel):
    school_name: str
    band: str
    margin: float
    reference_line: float
    years_observed: int
    lines: list[ReachMatchSafetyYearLineOut]
    department: str | None
    province: str | None
    zone: str | None
    is_985: bool
    is_211: bool
    is_self_drawn: bool
    source_file: str


class ReachMatchSafetyOut(BaseModel):
    year_to: int | None
    window: int
    score: float
    program_code: str | None
    program_name: str | None
    coverage_warning: str | None
    disclaimer: str
    rows: list[ReachMatchSafetyRowOut]


class HeatRankingRowOut(BaseModel):
    rank: int
    school_name: str
    college: str
    direction: str
    subject_class: str | None
    province: str | None
    region: str | None
    tier: str | None
    heat_net: float | None
    heat_comp: float | None
    wd_count: float | None
    nn_rate_raw: str | None
    line_2026_value: float | None
    admit_cnt_value: float | None
    src_label: str | None
    source_file: str


class HeatRankingOut(BaseModel):
    sort: str
    filters: dict[str, str | None]
    excluded_missing: int
    disclaimer: str
    rows: list[HeatRankingRowOut]


class AiReportSectionOut(BaseModel):
    title: str
    points: list[str]


class AiReportDataRefOut(BaseModel):
    school: str
    band: str
    reference_line: float
    margin: float


class AiReportOut(BaseModel):
    summary: str
    sections: list[AiReportSectionOut]
    data_refs: list[AiReportDataRefOut]
    style: str
    generated_by: str
    disclaimer: str
    session_id: int


class AiReportRequest(BaseModel):
    score: float
    program_code: str | None = None
    program_name: str | None = None
    year_to: int | None = None
    window: int = 3
    province: str | None = None
    zone: str | None = None
    is_985: bool | None = None
    is_211: bool | None = None
    style: str = "neutral"


class ProvinceOut(BaseModel):
    name: str
    school_count: int


class ProgramOptionOut(BaseModel):
    program_code: str
    program_name: str
    school_count: int


class ProgramSearchOut(BaseModel):
    query: str | None
    truncated: bool
    rows: list[ProgramOptionOut]
