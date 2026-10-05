"""School-name aliasing (GLOSSARY: 院校别名 SchoolAlias).

Different sources spell the same school differently, and schools are renamed
over time (e.g. 上海体育学院 → 上海体育大学). Queries resolve an alias to the
canonical name so either spelling hits. The default map covers known renames;
richer, data-driven aliases arrive with the cross-generation slice.
"""

from __future__ import annotations

DEFAULT_SCHOOL_ALIASES: dict[str, str] = {
    "上海体育学院": "上海体育大学",
    "海南医学院": "海南医科大学",
    "甘肃政法学院": "甘肃政法大学",
}


def resolve_school_alias(name: str) -> str:
    return DEFAULT_SCHOOL_ALIASES.get(name.strip(), name.strip())
