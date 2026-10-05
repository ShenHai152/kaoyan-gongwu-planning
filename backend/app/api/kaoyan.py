"""Read-only HTTP contract for the kaoyan domain."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.report import build_report
from app.db import get_sessionmaker
from app.domains.kaoyan.cs408_query import (
    list_cs408_conflicts,
    list_cs408_subject_changes,
    list_cs408_units,
    list_cs408_year_lines,
)
from app.domains.kaoyan.enrollment_query import list_enrollment_plans
from app.domains.kaoyan.heat_ranking import (
    DISCLAIMER as HEAT_DISCLAIMER,
)
from app.domains.kaoyan.heat_ranking import list_heat_ranking
from app.domains.kaoyan.national_line_query import list_national_lines
from app.domains.kaoyan.query import list_admission_lines
from app.domains.kaoyan.ranking import DISCLAIMER, list_program_ranking, locate_score
from app.domains.kaoyan.reach_match_safety import (
    DISCLAIMER as RMS_DISCLAIMER,
)
from app.domains.kaoyan.reach_match_safety import latest_year, list_reach_match_safety
from app.domains.kaoyan.reference import (
    PROGRAMS_DEFAULT_LIMIT,
    list_provinces,
    province_coverage_warning,
    search_programs,
    zone_coverage_warning,
)
from app.schemas.kaoyan import (
    AdmissionLineOut,
    AiReportOut,
    AiReportRequest,
    Cs408ConflictOut,
    Cs408SubjectChangeOut,
    Cs408UnitOut,
    Cs408YearLineOut,
    EnrollmentPlanOut,
    HeatRankingOut,
    NationalLineOut,
    ProgramRankingOut,
    ProgramSearchOut,
    ProvinceOut,
    ReachMatchSafetyOut,
)

router = APIRouter(prefix="/api/kaoyan", tags=["kaoyan"])


def get_session() -> Iterator[Session]:
    """Yield a session and always return its connection to the pool.

    Creating a session per request is only safe if it is also closed: an
    unclosed session holds a connection until garbage collection, and once the
    pool is exhausted every database request blocks and times out.
    """
    with get_sessionmaker()() as session:
        yield session


@router.get("/admission-lines", response_model=list[AdmissionLineOut])
def admission_lines(
    school: str = Query(...),
    program: str | None = None,
    degree_type: str | None = None,
    session: Session = Depends(get_session),
) -> list:
    return list_admission_lines(
        session, school=school, program=program, degree_type=degree_type
    )


@router.get("/provinces", response_model=list[ProvinceOut])
def provinces(session: Session = Depends(get_session)) -> list:
    return list_provinces(session)


@router.get("/programs", response_model=ProgramSearchOut)
def programs(
    query: str | None = None,
    limit: int = PROGRAMS_DEFAULT_LIMIT,
    session: Session = Depends(get_session),
) -> dict:
    return search_programs(session, query=query, limit=limit)


@router.get("/enrollment-plans", response_model=list[EnrollmentPlanOut])
def enrollment_plans(
    school: str = Query(...),
    program: str | None = None,
    study_mode: str | None = None,
    session: Session = Depends(get_session),
) -> list:
    return list_enrollment_plans(
        session, school=school, program=program, study_mode=study_mode
    )


@router.get("/national-lines", response_model=list[NationalLineOut])
def national_lines(
    year: int | None = None,
    subject: str | None = None,
    kind: str | None = None,
    session: Session = Depends(get_session),
) -> list:
    return list_national_lines(session, year=year, subject=subject, category_kind=kind)


@router.get("/cs408/units", response_model=list[Cs408UnitOut])
def cs408_units(
    school: str = Query(...),
    subject_class: str | None = None,
    session: Session = Depends(get_session),
) -> list:
    return list_cs408_units(session, school=school, subject_class=subject_class)


@router.get("/cs408/year-lines", response_model=list[Cs408YearLineOut])
def cs408_year_lines(
    school: str = Query(...),
    year: int | None = None,
    session: Session = Depends(get_session),
) -> list:
    return list_cs408_year_lines(session, school=school, year=year)


@router.get("/cs408/subject-changes", response_model=list[Cs408SubjectChangeOut])
def cs408_subject_changes(
    school: str = Query(...),
    session: Session = Depends(get_session),
) -> list:
    return list_cs408_subject_changes(session, school=school)


@router.get("/cs408/conflicts", response_model=list[Cs408ConflictOut])
def cs408_conflicts(
    school: str = Query(...),
    session: Session = Depends(get_session),
) -> list:
    return list_cs408_conflicts(session, school=school)


@router.get("/rankings/program", response_model=ProgramRankingOut)
def program_ranking(
    year: int = Query(...),
    program_code: str | None = None,
    program_name: str | None = None,
    score: float | None = None,
    zone: str | None = None,
    is_985: bool | None = None,
    is_211: bool | None = None,
    is_self_drawn: bool | None = None,
    session: Session = Depends(get_session),
) -> dict:
    if program_code is None and program_name is None:
        raise HTTPException(
            status_code=422, detail="program_code or program_name is required"
        )
    rows = list_program_ranking(
        session,
        year=year,
        program_code=program_code,
        program_name=program_name,
        zone=zone,
        is_985=is_985,
        is_211=is_211,
        is_self_drawn=is_self_drawn,
    )
    return {
        "year": year,
        "program_code": program_code,
        "program_name": program_name,
        "disclaimer": DISCLAIMER,
        "rows": rows,
        "position": locate_score(rows, score) if score is not None else None,
    }


@router.post("/ai-report", response_model=AiReportOut)
def ai_report(
    request: AiReportRequest,
    session: Session = Depends(get_session),
) -> dict:
    if request.program_code is None and request.program_name is None:
        raise HTTPException(
            status_code=422, detail="program_code or program_name is required"
        )
    if request.window < 1:
        raise HTTPException(status_code=422, detail="window must be >= 1")
    report = build_report(
        session,
        score=request.score,
        program_code=request.program_code,
        program_name=request.program_name,
        year_to=request.year_to,
        window=request.window,
        province=request.province,
        zone=request.zone,
        is_985=request.is_985,
        is_211=request.is_211,
        style=request.style,
    )
    session.commit()
    return report


@router.get("/heat-ranking", response_model=HeatRankingOut)
def heat_ranking(
    sort: str = Query("net", pattern="^(net|comp)$"),
    province: str | None = None,
    region: str | None = None,
    subject_class: str | None = None,
    tier: str | None = None,
    session: Session = Depends(get_session),
) -> dict:
    result = list_heat_ranking(
        session,
        sort=sort,
        province=province,
        region=region,
        subject_class=subject_class,
        tier=tier,
    )
    return {
        "sort": sort,
        "filters": {
            "province": province,
            "region": region,
            "subject_class": subject_class,
            "tier": tier,
        },
        "excluded_missing": result["excluded_missing"],
        "disclaimer": HEAT_DISCLAIMER,
        "rows": result["rows"],
    }


@router.get("/reach-match-safety", response_model=ReachMatchSafetyOut)
def reach_match_safety(
    score: float = Query(...),
    year_to: int | None = None,
    window: int = 3,
    program_code: str | None = None,
    program_name: str | None = None,
    province: list[str] | None = Query(None),
    zone: list[str] | None = Query(None),
    is_985: bool | None = None,
    is_211: bool | None = None,
    is_self_drawn: bool | None = None,
    session: Session = Depends(get_session),
) -> dict:
    if program_code is None and program_name is None:
        raise HTTPException(
            status_code=422, detail="program_code or program_name is required"
        )
    if window < 1:
        raise HTTPException(status_code=422, detail="window must be >= 1")
    # Resolve the default window end exactly once, inside the owner.
    resolved_year = year_to if year_to is not None else latest_year(session)
    rows = (
        list_reach_match_safety(
            session,
            score=score,
            year_to=resolved_year,
            window=window,
            program_code=program_code,
            program_name=program_name,
            province=province,
            zone=zone,
            is_985=is_985,
            is_211=is_211,
            is_self_drawn=is_self_drawn,
        )
        if resolved_year is not None
        else []
    )
    coverage_warnings: list[str] = []
    if resolved_year is not None:
        province_warning = province_coverage_warning(
            session, year_to=resolved_year, window=window, province=province
        )
        if province_warning:
            coverage_warnings.append(province_warning)
        zone_warning = zone_coverage_warning(
            session, year_to=resolved_year, window=window, zone=zone
        )
        if zone_warning:
            coverage_warnings.append(zone_warning)
    return {
        "year_to": resolved_year,
        "window": window,
        "score": score,
        "program_code": program_code,
        "program_name": program_name,
        "coverage_warning": " ".join(coverage_warnings) or None,
        "disclaimer": RMS_DISCLAIMER,
        "rows": rows,
    }
