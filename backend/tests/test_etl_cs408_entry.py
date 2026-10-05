"""Exercise the ETL adapter entry point, not just the domain loader."""

import json

from sqlalchemy import create_engine, func, select

from app.db import Base
from app.domains.kaoyan.models import (
    Cs408Conflict,
    Cs408SubjectChange,
    Cs408Unit,
    Cs408YearLine,
)
from etl.kaoyan.load_cs408_units import run


def test_run_loads_all_tables(tmp_path):
    schools = tmp_path / "schools"
    schools.mkdir()
    payload = {
        "name": "测试大学",
        "units": [
            {
                "college": "计算机学院",
                "direction": "不区分",
                "subjectClass": "22408",
                "linesByYear": {"2025": "300", "2026": "310"},
            }
        ],
        "conflicts": [{"field": "subjectClass", "old": "22408", "new": "11408"}],
        "updates2027": [{"专业/范围": "计院", "新科目": "408", "生效年份": "2027"}],
    }
    (schools / "001-测试大学.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    engine = _engine(tmp_path)
    stats = run(engine, schools)
    assert stats == {
        "files": 1,
        "units": 1,
        "year_lines": 2,
        "conflicts": 1,
        "subject_changes": 1,
    }

    from sqlalchemy.orm import sessionmaker

    with sessionmaker(bind=engine)() as session:
        assert session.scalar(select(func.count()).select_from(Cs408Unit)) == 1
        assert session.scalar(select(func.count()).select_from(Cs408YearLine)) == 2
        assert session.scalar(select(func.count()).select_from(Cs408Conflict)) == 1
        assert (
            session.scalar(select(func.count()).select_from(Cs408SubjectChange)) == 1
        )


def test_empty_or_missing_dir_fails_loud(tmp_path):
    import pytest

    engine = _engine(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    for directory in (empty, tmp_path / "does-not-exist"):
        with pytest.raises(FileNotFoundError):
            run(engine, directory)


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'etl.db'}")
    Base.metadata.create_all(engine)
    return engine
