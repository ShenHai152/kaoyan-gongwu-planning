from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domains.kaoyan.models import Cs408Unit
from app.main import app, get_session


def make_client(engine) -> TestClient:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        session.add_all(
            [
                Cs408Unit(
                    school_name="甲大学", college="计算机学院", direction="不区分研究方向",
                    province="广东", region="华南", tier="双非", subject_class="11408",
                    heat_net=88.0, heat_comp=65.0, wd_count=8.0, nn_rate_raw="80%",
                    line_2026_value=335.0, admit_cnt_value=11.0, src_label="官方",
                    source_file="a.json",
                ),
                Cs408Unit(
                    school_name="乙大学", college="软件学院", direction="不区分研究方向",
                    province="北京", region="华北", tier="985", subject_class="11408",
                    heat_net=None, heat_comp=90.0, source_file="b.json",
                ),
            ]
        )
        session.commit()
    app.dependency_overrides[get_session] = lambda: factory()
    return TestClient(app)


def test_heat_ranking_endpoint(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/heat-ranking", params={"sort": "net"})
    assert r.status_code == 200
    body = r.json()
    assert body["sort"] == "net"
    assert body["excluded_missing"] == 1
    assert body["disclaimer"]
    assert [row["school_name"] for row in body["rows"]] == ["甲大学"]
    row = body["rows"][0]
    assert row["rank"] == 1
    assert row["heat_net"] == 88.0
    assert row["wd_count"] == 8.0
    assert row["nn_rate_raw"] == "80%"
    assert row["source_file"] == "a.json"


def test_heat_ranking_filter(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/heat-ranking", params={"sort": "comp", "tier": "985"})
    body = r.json()
    assert [row["school_name"] for row in body["rows"]] == ["乙大学"]


def test_heat_ranking_unknown_filter_empty(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/heat-ranking", params={"province": "火星"})
    assert r.status_code == 200
    assert r.json()["rows"] == []


def test_heat_ranking_invalid_sort(engine):
    client = make_client(engine)
    r = client.get("/api/kaoyan/heat-ranking", params={"sort": "bogus"})
    assert r.status_code == 422
