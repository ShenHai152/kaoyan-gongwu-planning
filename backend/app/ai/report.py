"""Assemble an admission report from kaoyan data and an LLM provider.

The report is narrative over the kaoyan read-time projections (reach / match /
safety, score rank, 408 heat). It never invents numbers: every figure in
`data_refs` comes straight from a kaoyan query. When no provider is configured
or the call fails, a template report is returned instead of an error.

Style (`neutral` / `xuefeng`) changes wording only. Neither style impersonates
Zhang Xuefeng, uses profanity, or predicts admission probability.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai import sessions
from app.domains.kaoyan.heat_ranking import list_heat_ranking
from app.domains.kaoyan.ranking import list_program_ranking, locate_score
from app.domains.kaoyan.reach_match_safety import latest_year, list_reach_match_safety
from app.llm import LLMRequest, LLMUnavailable, resolve

DISCLAIMER = (
    "本报告为基于系统内历年公开数据的分析与建议，不预测录取概率，"
    "不代表最终录取结果；报名决策以当年官方招生简章/研招网目录/学院公示为准。"
)

_XUEFENG_STYLE_NOTE = (
    "本报告采用基于张雪峰公开方法论的**分析风格**（结论先行、数据说话、"
    "看中位数），不代表其本人观点，系统不模拟其人格。"
)

STYLES = ("neutral", "xuefeng")


def _methodology_lines(style: str) -> list[str]:
    lines = [
        "分析要求：结论先行，先给判断再给依据；引用具体数据，不说空话；",
        "看普通毕业生的中位数情况，而非明星案例。",
    ]
    if style == "xuefeng":
        lines.append(_XUEFENG_STYLE_NOTE)
    return lines


def collect_data(
    session: Session,
    *,
    score: float,
    program_code: str | None,
    program_name: str | None,
    year_to: int | None,
    window: int,
    province: str | None = None,
    zone: str | None = None,
    is_985: bool | None = None,
    is_211: bool | None = None,
) -> dict:
    """Gather the kaoyan projections the report is allowed to cite."""
    resolved_year = year_to if year_to is not None else latest_year(session)
    bands: list[dict] = []
    if resolved_year is not None:
        bands = list_reach_match_safety(
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
        )
    ranking: list[dict] = []
    position: dict | None = None
    if resolved_year is not None:
        ranking = list_program_ranking(
            session,
            year=resolved_year,
            program_code=program_code,
            program_name=program_name,
            zone=zone,
            is_985=is_985,
            is_211=is_211,
        )
        position = locate_score(ranking, score)
    return {
        "year_to": resolved_year,
        "bands": bands,
        "ranking": ranking,
        "position": position,
        "heat": list_heat_ranking(session, sort="net")["rows"][:10],
    }


def _band_counts(bands: list[dict]) -> dict[str, int]:
    counts = {"reach": 0, "match": 0, "safety": 0}
    for row in bands:
        counts[row["band"]] = counts.get(row["band"], 0) + 1
    return counts


def _build_prompt(
    *, score: float, program_code: str | None, program_name: str | None, data: dict, style: str
) -> str:
    label = program_code or program_name or "（未指定专业）"
    counts = _band_counts(data["bands"])
    facts = {
        "score": score,
        "program": label,
        "year_to": data["year_to"],
        "band_counts": counts,
        "position": data["position"],
        "top_reference_lines": [
            {
                "school": row["school_name"],
                "band": row["band"],
                "reference_line": row["reference_line"],
                "margin": row["margin"],
            }
            for row in sorted(data["bands"], key=lambda r: r["margin"])[:8]
        ],
        "hot_408": [
            {"school": row["school_name"], "heat_net": row["heat_net"]}
            for row in data["heat"]
        ],
    }
    instructions = "\n".join(_methodology_lines(style))
    return (
        f"考生分数：{score}；报考专业：{label}。\n"
        f"{instructions}\n"
        "以下是系统内真实数据（仅可引用这些数字，不得编造）：\n"
        f"{json.dumps(facts, ensure_ascii=False)}\n"
        "请输出 JSON：{summary, sections: [{title, points}], data_refs}。"
        "禁止输出录取概率，禁止第一人称冒充他人，禁止粗口。"
    )


def _template_report(
    *, score: float, program_code: str | None, program_name: str | None, data: dict, style: str
) -> dict:
    label = program_code or program_name or "（未指定专业）"
    counts = _band_counts(data["bands"])
    summary = (
        f"{score} 分报考 {label}：冲刺 {counts['reach']} 所、稳妥 {counts['match']} 所、"
        f"保底 {counts['safety']} 所（{data['year_to']} 年窗口）。"
    )
    sections = [
        {
            "title": "档位分布",
            "points": [
                f"冲刺 {counts['reach']} 所、稳妥 {counts['match']} 所、保底 {counts['safety']} 所。"
            ],
        }
    ]
    position = data["position"]
    if position is not None:
        sections.append(
            {
                "title": "分数位次",
                "points": [
                    (
                        f"该分数在当年榜单中超过 {position['schools_passing']} 所院校的线，"
                        f"共 {position['total_schools']} 所。"
                    )
                ],
            }
        )
    refs = [
        {
            "school": row["school_name"],
            "band": row["band"],
            "reference_line": row["reference_line"],
            "margin": row["margin"],
        }
        for row in data["bands"]
    ]
    return {
        "summary": summary,
        "sections": sections,
        "data_refs": refs,
        "style": style,
        "generated_by": "template",
        "disclaimer": DISCLAIMER,
    }


def _parse_completion(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_sections(raw: object) -> list[dict]:
    """Coerce model output to the report shape; drop anything malformed.

    The completion is untrusted: a section may arrive as a bare string or with
    a non-list `points`. Normalizing here keeps a bad completion from turning
    the response into a 500.
    """
    if not isinstance(raw, list):
        return []
    sections: list[dict] = []
    for item in raw:
        if isinstance(item, str):
            sections.append({"title": item, "points": []})
        elif isinstance(item, dict) and isinstance(item.get("title"), str):
            points = item.get("points")
            sections.append(
                {
                    "title": item["title"],
                    "points": [p for p in points if isinstance(p, str)]
                    if isinstance(points, list)
                    else [],
                }
            )
    return sections


def build_report(
    session: Session,
    *,
    score: float,
    program_code: str | None,
    program_name: str | None,
    year_to: int | None = None,
    window: int = 3,
    province: str | None = None,
    zone: str | None = None,
    is_985: bool | None = None,
    is_211: bool | None = None,
    style: str = "neutral",
    provider=None,
) -> dict:
    if style not in STYLES:
        raise ValueError("style must be 'neutral' or 'xuefeng'")

    data = collect_data(
        session,
        score=score,
        program_code=program_code,
        program_name=program_name,
        year_to=year_to,
        window=window,
        province=province,
        zone=zone,
        is_985=is_985,
        is_211=is_211,
    )
    prompt = _build_prompt(
        score=score,
        program_code=program_code,
        program_name=program_name,
        data=data,
        style=style,
    )
    system = "你是考研择校数据分析助手。" + (
        " " + _XUEFENG_STYLE_NOTE if style == "xuefeng" else ""
    )

    if provider is None:
        try:
            provider = resolve()
        except LLMUnavailable:
            provider = None

    record = sessions.start_session(
        session,
        kind="admission-report",
        provider=getattr(provider, "name", "none"),
        style=style,
    )
    sessions.append_event(
        session, session_id=record.id, event_type="prompt", payload={"system": system, "user": prompt}
    )
    sessions.append_event(session, session_id=record.id, event_type="input", payload=data)

    if provider is None:
        report = _template_report(
            score=score,
            program_code=program_code,
            program_name=program_name,
            data=data,
            style=style,
        )
        sessions.append_event(
            session,
            session_id=record.id,
            event_type="response",
            payload={"generated_by": "template", "report": report},
        )
        report["session_id"] = record.id
        return report

    try:
        completion = provider.complete(
            LLMRequest(system=system, user=prompt, json_output=True)
        )
    except (LLMUnavailable, ValueError, KeyError, TypeError) as exc:
        # A provider failure must fall back to the template, not 500. Adapters
        # already translate transport errors into LLMUnavailable; the rest
        # guard against a malformed provider payload.
        sessions.append_event(
            session,
            session_id=record.id,
            event_type="error",
            payload={"error": repr(exc)},
        )
        report = _template_report(
            score=score,
            program_code=program_code,
            program_name=program_name,
            data=data,
            style=style,
        )
        sessions.append_event(
            session,
            session_id=record.id,
            event_type="response",
            payload={"generated_by": "template", "report": report},
        )
        report["session_id"] = record.id
        return report

    sessions.append_event(
        session,
        session_id=record.id,
        event_type="completion",
        payload={"model": completion.model, "usage": completion.usage, "text": completion.text},
    )

    parsed = _parse_completion(completion.text)
    if parsed is None:
        report = _template_report(
            score=score,
            program_code=program_code,
            program_name=program_name,
            data=data,
            style=style,
        )
    else:
        # The model may only narrate; the cited data stays the system's.
        report = {
            "summary": parsed.get("summary")
            if isinstance(parsed.get("summary"), str)
            else "",
            "sections": _normalize_sections(parsed.get("sections")),
            "data_refs": _template_report(
                score=score,
                program_code=program_code,
                program_name=program_name,
                data=data,
                style=style,
            )["data_refs"],
            "style": style,
            "generated_by": f"llm:{completion.model}",
            "disclaimer": DISCLAIMER,
        }
    sessions.append_event(
        session, session_id=record.id, event_type="response", payload={"report": report}
    )
    report["session_id"] = record.id
    return report
