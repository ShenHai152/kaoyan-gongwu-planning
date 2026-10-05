from app.domains.kaoyan.heat_ranking import list_heat_ranking
from app.domains.kaoyan.models import Cs408Unit


def _unit(session, **overrides) -> Cs408Unit:
    defaults = {
        "school_name": "占位大学",
        "college": "计算机学院",
        "direction": "不区分研究方向",
        "province": "广东",
        "region": "华南",
        "tier": "双非",
        "subject_class": "11408",
        "heat_net": 50.0,
        "heat_comp": 50.0,
        "source_file": "x.json",
    }
    defaults.update(overrides)
    unit = Cs408Unit(**defaults)
    session.add(unit)
    session.flush()
    return unit


def test_orders_by_heat_net_desc(session):
    _unit(session, school_name="甲大学", heat_net=88.0)
    _unit(session, school_name="乙大学", heat_net=65.0)
    _unit(session, school_name="丙大学", heat_net=30.0)
    result = list_heat_ranking(session, sort="net")
    assert [r["school_name"] for r in result["rows"]] == ["甲大学", "乙大学", "丙大学"]
    assert [r["rank"] for r in result["rows"]] == [1, 2, 3]
    assert result["excluded_missing"] == 0


def test_ties_share_rank_and_break_by_school_name(session):
    _unit(session, school_name="乙大学", heat_net=70.0)
    _unit(session, school_name="甲大学", heat_net=70.0)
    _unit(session, school_name="丙大学", heat_net=10.0)
    result = list_heat_ranking(session, sort="net")
    assert [r["school_name"] for r in result["rows"]] == ["乙大学", "甲大学", "丙大学"]
    assert [r["rank"] for r in result["rows"]] == [1, 1, 3]


def test_sort_by_competition_heat(session):
    _unit(session, school_name="甲大学", heat_net=10.0, heat_comp=90.0)
    _unit(session, school_name="乙大学", heat_net=99.0, heat_comp=20.0)
    result = list_heat_ranking(session, sort="comp")
    assert [r["school_name"] for r in result["rows"]] == ["甲大学", "乙大学"]


def test_missing_sort_key_excluded_and_counted(session):
    _unit(session, school_name="甲大学", heat_net=80.0)
    _unit(session, school_name="乙大学", heat_net=None)
    _unit(session, school_name="丙大学", heat_net=None)
    result = list_heat_ranking(session, sort="net")
    assert [r["school_name"] for r in result["rows"]] == ["甲大学"]
    assert result["excluded_missing"] == 2


def test_filters_before_ranking(session):
    _unit(session, school_name="甲大学", province="广东", tier="双非", heat_net=10.0)
    _unit(session, school_name="乙大学", province="北京", tier="985", heat_net=90.0)
    result = list_heat_ranking(session, sort="net", province="广东")
    assert [r["school_name"] for r in result["rows"]] == ["甲大学"]
    assert result["rows"][0]["rank"] == 1


def test_unknown_filter_returns_empty(session):
    _unit(session, school_name="甲大学", province="广东")
    result = list_heat_ranking(session, sort="net", province="火星")
    assert result["rows"] == []
    assert result["excluded_missing"] == 0


def test_invalid_sort_rejected(session):
    import pytest

    with pytest.raises(ValueError):
        list_heat_ranking(session, sort="bogus")
