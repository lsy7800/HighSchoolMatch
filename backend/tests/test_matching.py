"""Tests for the matching engine + public API, against the seeded 2025 data.

Run from backend/:  python -m pytest -q
Requires the DB to be seeded first (scripts.seed_2025).
"""
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.matching import classify, rank_to_equiv_score, recommend, score_to_rank

DEFAULT_CFG = {"stable_margin": 0.10, "safe_floor": 0.5, "reach_ceiling": 1.5}


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---- 位次换算: 用天津一中已知值锚定 ----
def test_score_to_rank_known_value(db):
    # 一中 2025 录取最低分 768.9 -> 768档: 市区1193 / 全市1557
    r = score_to_rank(db, 768.9, 2025)
    assert r.floor_score == 768
    assert r.rank_city6 == 1193
    assert r.rank_whole == 1557
    assert r.out_of_range is False


def test_score_floor(db):
    # 小数应向下取整到整数档
    assert score_to_rank(db, 768.0, 2025).rank_city6 == 1193
    assert score_to_rank(db, 768.99, 2025).rank_city6 == 1193


def test_out_of_range(db):
    assert score_to_rank(db, 800, 2025).out_of_range is True
    assert score_to_rank(db, 400, 2025).out_of_range is True
    # 夹取到边界仍返回有效位次
    assert score_to_rank(db, 800, 2025).rank_city6 == score_to_rank(db, 780, 2025).rank_city6


def test_equiv_score_roundtrip(db):
    # 市区位次1193 反查市区列 -> 768
    assert rank_to_equiv_score(db, 1193, 2025, scope_whole=False) == 768
    # 全市位次1557 反查全市列 -> 768
    assert rank_to_equiv_score(db, 1557, 2025, scope_whole=True) == 768


# ---- 分类逻辑 ----
def test_classify_buckets():
    # 学生位次==学校位次 -> 稳
    assert classify(1000, 1000, DEFAULT_CFG) == "stable"
    # 学生明显靠前(位次小) -> 保
    assert classify(700, 1000, DEFAULT_CFG) == "safe"
    # 学生靠后(位次大)但在可冲范围 -> 冲
    assert classify(1300, 1000, DEFAULT_CFG) == "reach"
    # 差距过大 -> 不推荐
    assert classify(2000, 1000, DEFAULT_CFG) is None
    assert classify(100, 1000, DEFAULT_CFG) is None


# ---- 推荐主流程 ----
def test_recommend_structure(db):
    res = recommend(db, 720, 2025)
    assert res["rank_city6"] > 0 and res["rank_whole"] > 0
    assert set(["reach", "stable", "safe"]).issubset(res.keys())
    # 一中(768.9)对720分考生应属"冲"档(学生位次远大于一中位次1193)
    all_names = {x["name"] for bucket in ("reach", "stable", "safe") for x in res[bucket]}
    # 至少应能匹配到一些学校
    assert len(all_names) > 0


def test_recommend_scope_uses_right_rank(db):
    # 市内六区学校应使用学生市区位次, 全市/郊区使用全市位次
    res = recommend(db, 720, 2025)
    for bucket in ("reach", "stable", "safe"):
        for x in res[bucket]:
            if x["scope"] == "city6":
                assert x["student_rank"] == res["rank_city6"]
            else:
                assert x["student_rank"] == res["rank_whole"]


def test_suburb_excluded(db):
    # 市内六区考生不能填报郊区招生学校: 任何分数/模式下结果都不应含 suburb
    for score in (720, 600, 450):
        res = recommend(db, score, 2025)
        for bucket in ("reach", "stable", "safe", "reachable"):
            assert all(x["scope"] != "suburb" for x in res.get(bucket, []))


def test_low_score_mode(db):
    # 低于最低档(500)的分数: 触发低分模式, 不分冲稳保, 给 reachable 列表
    res = recommend(db, 450, 2025)
    assert res["low_score_mode"] is True
    assert res["reach"] == [] and res["stable"] == [] and res["safe"] == []
    assert len(res["reachable"]) > 0
    # reachable 按录取门槛从低到高(school_rank 降序: 位次越大门槛越低)
    ranks = [x["school_rank"] for x in res["reachable"]]
    assert ranks == sorted(ranks, reverse=True)


def test_normal_mode_not_low(db):
    # 正常分数不应进低分模式
    res = recommend(db, 720, 2025)
    assert res["low_score_mode"] is False
    assert res["reachable"] == []
    # 恰好在最低档(500)也不算低分模式
    assert recommend(db, 500, 2025)["low_score_mode"] is False


# ---- API ----
def test_api_years(client):
    r = client.get("/api/years")
    assert r.status_code == 200
    assert 2025 in r.json()


def test_api_recommend(client):
    r = client.post("/api/recommend", json={"score": 720})
    assert r.status_code == 200
    body = r.json()
    assert body["year"] == 2025
    assert "stable" in body


def test_api_school_detail(client):
    r = client.get("/api/schools/10101")  # 天津一中
    assert r.status_code == 200
    body = r.json()
    assert body[0]["name"] == "★天津一中"
    s2025 = next(s for s in body[0]["stats"] if s["year"] == 2025)
    assert s2025["rank_city6"] == 1193


def test_api_school_not_found(client):
    assert client.get("/api/schools/00000").status_code == 404
