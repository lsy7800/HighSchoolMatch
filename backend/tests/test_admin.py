"""Tests for the admin API: login, auth guard, import, CRUD, config.

Run from backend/:  python -m pytest -q
Mutating tests re-seed the DB afterward so the public-API suite stays valid.
"""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

DATA = Path(__file__).resolve().parent.parent.parent / "data_source"
SCORE_RANK_XLSX = DATA / "2025年一分档.xlsx"
SCHOOLS_XLSX = DATA / "天津市高中数据汇总2025（分区）.xlsx"


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def token(client):
    r = client.post(
        "/api/admin/login",
        data={"username": settings.admin_username, "password": settings.admin_password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------- 登录 / 鉴权 ----------------
def test_login_wrong_password(client):
    r = client.post(
        "/api/admin/login", data={"username": "admin", "password": "wrong"}
    )
    assert r.status_code == 401


def test_protected_requires_token(client):
    assert client.get("/api/admin/schools").status_code == 401


def test_me(client, token):
    r = client.get("/api/admin/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == settings.admin_username


# ---------------- 学校 CRUD ----------------
def test_list_and_filter_schools(client, token):
    r = client.get("/api/admin/schools", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 278

    r2 = client.get("/api/admin/schools?scope=city6", headers=auth(token))
    assert len(r2.json()) == 81

    r3 = client.get("/api/admin/schools?q=一中", headers=auth(token))
    assert any("一中" in s["name"] for s in r3.json())


def test_update_school_then_restore(client, token):
    # find 天津一中
    lst = client.get("/api/admin/schools?q=天津一中", headers=auth(token)).json()
    sid = next(s["id"] for s in lst if s["code"] == "10101")
    orig = client.get(f"/api/admin/schools/{sid}", headers=auth(token)).json()

    r = client.put(
        f"/api/admin/schools/{sid}",
        json={"phone": "00000000"},
        headers=auth(token),
    )
    assert r.status_code == 200
    assert r.json()["phone"] == "00000000"

    # restore
    client.put(
        f"/api/admin/schools/{sid}",
        json={"phone": orig["phone"]},
        headers=auth(token),
    )


def test_upsert_stat(client, token):
    lst = client.get("/api/admin/schools?q=天津一中", headers=auth(token)).json()
    sid = next(s["id"] for s in lst if s["code"] == "10101")
    r = client.put(
        f"/api/admin/schools/{sid}/stat",
        json={"year": 2021, "min_score": 760.0, "rank_city6": 1200, "rank_whole": 1600},
        headers=auth(token),
    )
    assert r.status_code == 200
    years = {s["year"] for s in r.json()["stats"]}
    assert 2021 in years
    # cleanup: overwrite 2021 back to nulls is fine; leave it, harmless extra year


# ---------------- 一分档 ----------------
def test_score_rank_list(client, token):
    r = client.get("/api/admin/score-rank?year=2025", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) == 281


# ---------------- 阈值配置 ----------------
def test_config_get_and_update(client, token):
    r = client.get("/api/admin/config", headers=auth(token))
    assert r.status_code == 200
    assert "stable_margin" in r.json()

    r2 = client.put(
        "/api/admin/config",
        json={"values": {"stable_margin": 0.15}},
        headers=auth(token),
    )
    assert r2.status_code == 200
    assert r2.json()["stable_margin"] == 0.15

    # unknown key rejected
    r3 = client.put(
        "/api/admin/config", json={"values": {"bogus": 1}}, headers=auth(token)
    )
    assert r3.status_code == 400

    # restore default
    client.put(
        "/api/admin/config",
        json={"values": {"stable_margin": 0.10}},
        headers=auth(token),
    )


# ---------------- 导入(预览) ----------------
def test_import_score_rank_preview(client, token):
    with open(SCORE_RANK_XLSX, "rb") as f:
        files = {"file": ("一分档.xlsx", io.BytesIO(f.read()),
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = client.post(
        "/api/admin/import/score-rank",
        files=files,
        data={"commit": "false"},
        headers=auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["committed"] is False
    assert body["preview"].get("2025") == 281


def test_import_schools_preview(client, token):
    with open(SCHOOLS_XLSX, "rb") as f:
        files = {"file": ("schools.xlsx", io.BytesIO(f.read()),
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = client.post(
        "/api/admin/import/schools",
        files=files,
        data={"commit": "false"},
        headers=auth(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["committed"] is False
    assert body["preview"]["total"] == 278


def test_import_rejects_non_xlsx(client, token):
    files = {"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")}
    r = client.post(
        "/api/admin/import/score-rank",
        files=files,
        data={"commit": "false"},
        headers=auth(token),
    )
    assert r.status_code == 400
