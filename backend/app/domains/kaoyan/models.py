"""Authoritative state for the kaoyan domain: yearly admission lines."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AdmissionLine(Base):
    __tablename__ = "kaoyan_admission_line"
    __table_args__ = (
        UniqueConstraint(
            "school_name",
            "program_code",
            "program_name",
            "degree_type",
            "year",
            "department",
            name="uq_kaoyan_admission_line_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(128), index=True)
    school_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    program_name: Mapped[str] = mapped_column(String(128), index=True)
    program_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    degree_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    political: Mapped[float | None] = mapped_column(Float, nullable=True)
    foreign_language: Mapped[float | None] = mapped_column(Float, nullable=True)
    subject_one: Mapped[float | None] = mapped_column(Float, nullable=True)
    subject_two: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_delta_raw: Mapped[str | None] = mapped_column(String(16), nullable=True)
    province: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_985: Mapped[bool] = mapped_column(Boolean, default=False)
    is_211: Mapped[bool] = mapped_column(Boolean, default=False)
    is_double_first_class: Mapped[bool] = mapped_column(Boolean, default=False)
    zone: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_self_drawn: Mapped[bool] = mapped_column(Boolean, default=False)
    website: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))
    source_row: Mapped[int] = mapped_column(Integer)


class EnrollmentPlan(Base):
    """Yearly enrollment plan (招生计划): how many each direction admits."""

    __tablename__ = "kaoyan_enrollment_plan"
    __table_args__ = (
        UniqueConstraint(
            "school_name",
            "program_name",
            "study_mode",
            "direction",
            "year",
            name="uq_kaoyan_enrollment_plan_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(128), index=True)
    school_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    program_name: Mapped[str] = mapped_column(String(160), index=True)
    program_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    department: Mapped[str | None] = mapped_column(String(160), nullable=True)
    degree_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    study_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(256), nullable=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    enrollment_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    enrollment_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enrollment_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    exam_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exam_subjects: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(32), nullable=True)
    province: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_985: Mapped[bool] = mapped_column(Boolean, default=False)
    is_211: Mapped[bool] = mapped_column(Boolean, default=False)
    is_double_first_class: Mapped[bool] = mapped_column(Boolean, default=False)
    zone: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_self_drawn: Mapped[bool] = mapped_column(Boolean, default=False)
    source_file: Mapped[str] = mapped_column(String(256))
    source_row: Mapped[int] = mapped_column(Integer)


class NationalLine(Base):
    """National minimum score line (国家线), A/B candidate types by year."""

    __tablename__ = "kaoyan_national_line"
    __table_args__ = (
        UniqueConstraint(
            "year",
            "category_kind",
            "subject",
            "candidate_type",
            name="uq_kaoyan_national_line_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    category_kind: Mapped[str] = mapped_column(String(16), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    candidate_type: Mapped[str] = mapped_column(String(2), index=True)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    single_100: Mapped[float | None] = mapped_column(Float, nullable=True)
    single_over100: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_url: Mapped[str] = mapped_column(String(256))
    retrieved_at: Mapped[str] = mapped_column(String(40))


class Cs408Unit(Base):
    """408-track admission unit: school x college x direction (GLOSSARY: Cs408Unit).

    Independent from AdmissionLine/EnrollmentPlan: its caliber is a single
    college/direction (e.g. 085410 AI), not the school-wide program, and it is
    third-party curated (CC BY 4.0). Never mixed with the wide-caliber tables.
    """

    __tablename__ = "kaoyan_cs408_unit"
    __table_args__ = (
        UniqueConstraint(
            "school_name",
            "college",
            "direction",
            name="uq_kaoyan_cs408_unit_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(128), index=True)
    college: Mapped[str] = mapped_column(String(160))
    direction: Mapped[str] = mapped_column(String(256))
    category: Mapped[str | None] = mapped_column(String(16), nullable=True)
    province: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subject_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    line2026_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    line_2026_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    line_delta_raw: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plan2026_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    plan2026_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    fill_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retest_cnt_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retest_cnt_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    admit_cnt_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admit_cnt_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    admit_max_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admit_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    admit_min_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admit_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    admit_avg_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admit_avg_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    heat_net: Mapped[float | None] = mapped_column(Float, nullable=True)
    heat_comp: Mapped[float | None] = mapped_column(Float, nullable=True)
    nn_408_avg_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nn_408_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    nn_rate_raw: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_tag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    note: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    src_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    kaoqing_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    wd_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))


class Cs408YearLine(Base):
    """One year's retest line for a Cs408Unit; raw text and parsed value coexist.

    The owning unit is referenced by foreign key: a line cannot exist without a
    unit, and the (unit, year) pair is the business key.
    """

    __tablename__ = "kaoyan_cs408_year_line"
    __table_args__ = (
        UniqueConstraint(
            "unit_id", "year", name="uq_kaoyan_cs408_year_line_business_key"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("kaoyan_cs408_unit.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer, index=True)
    line_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    line_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))


class Cs408Conflict(Base):
    """A caliber conflict registered upstream (GLOSSARY: ConflictClaim).

    Two upstream shapes share this table: the old/new form and the claims form.
    `claims_json` / `sources_json` keep the nested payload verbatim so nothing is
    lost; a conflict is a warning that must be read before using the numbers.
    """

    __tablename__ = "kaoyan_cs408_conflict"
    __table_args__ = (
        UniqueConstraint(
            "school_name",
            "ordinal",
            name="uq_kaoyan_cs408_conflict_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(128), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    field: Mapped[str] = mapped_column(String(160))
    unit: Mapped[str] = mapped_column(String(160), default="")
    old_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    claims_json: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    sources_json: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))


class Cs408SubjectChange(Base):
    """A 2027 exam-subject change announced upstream (`updates2027`)."""

    __tablename__ = "kaoyan_cs408_subject_change"
    __table_args__ = (
        UniqueConstraint(
            "school_name",
            "scope",
            "effective_year",
            name="uq_kaoyan_cs408_subject_change_business_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String(128), index=True)
    tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scope: Mapped[str] = mapped_column(String(256))
    old_subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    new_subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    effective_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    note: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_file: Mapped[str] = mapped_column(String(256))
