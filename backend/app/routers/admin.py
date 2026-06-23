"""Admin API: login, xlsx import (preview/commit), CRUD, config.

All routes except /login require a valid bearer token (get_current_admin).
"""
import io

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from .. import matching
from ..auth import create_token, get_current_admin, verify_credentials
from ..database import get_db
from ..importers.schools_xlsx import import_schools, parse_schools
from ..importers.score_rank_xlsx import import_score_rank, parse_score_rank
from ..models import SCOPE_CITY6, SCOPE_SUBURB, SCOPE_WHOLE, AppConfig, School, SchoolStat, ScoreRank
from ..schemas import (
    ConfigUpdate,
    ScoreRankUpdate,
    SchoolCreate,
    SchoolDetail,
    SchoolListItem,
    SchoolUpdate,
    StatUpsert,
    YearStat,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------- 登录 ----------------
@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if not verify_credentials(username, password):
        raise HTTPException(401, "用户名或密码错误")
    return {"access_token": create_token(username), "token_type": "bearer"}


@router.get("/me")
def me(admin: str = Depends(get_current_admin)):
    return {"username": admin}


# ---------------- xlsx 导入 ----------------
def _read_upload(file: UploadFile) -> io.BytesIO:
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "请上传 .xlsx 文件")
    data = file.file.read()
    if not data:
        raise HTTPException(400, "文件为空")
    return io.BytesIO(data)


@router.post("/import/score-rank")
def import_score_rank_endpoint(
    file: UploadFile = File(...),
    commit: bool = Form(False),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """上传一分档 xlsx。commit=false 仅预览, commit=true 按年份替换入库。"""
    buf = _read_upload(file)
    try:
        parsed = parse_score_rank(buf)
    except Exception as e:
        raise HTTPException(400, f"解析失败: {e}")

    preview = {year: len(rows) for year, rows in parsed.items()}
    if not commit:
        return {"committed": False, "preview": preview, "years": list(preview)}

    buf.seek(0)
    counts = import_score_rank(db, buf)
    return {"committed": True, "imported": counts}


@router.post("/import/schools")
def import_schools_endpoint(
    file: UploadFile = File(...),
    commit: bool = Form(False),
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """上传高中数据 xlsx(三 sheet)。commit=false 仅预览, commit=true 全量替换。"""
    buf = _read_upload(file)
    try:
        parsed = parse_schools(buf)
    except Exception as e:
        raise HTTPException(400, f"解析失败: {e}")

    from collections import Counter

    by_scope = Counter(s["scope"] for s in parsed)
    preview = {"total": len(parsed), "by_scope": dict(by_scope)}
    if not commit:
        return {"committed": False, "preview": preview}

    buf.seek(0)
    counts = import_schools(db, buf)
    return {"committed": True, "imported": counts}


# ---------------- 学校 CRUD ----------------
def _school_to_detail(s: School) -> SchoolDetail:
    stats = sorted(s.stats, key=lambda x: x.year, reverse=True)
    return SchoolDetail(
        code=s.code, name=s.name, scope=s.scope, type=s.type,
        home_district=s.home_district, location_district=s.location_district,
        recruit_area=s.recruit_area, boarding=s.boarding, canteen=s.canteen,
        class_types=s.class_types, fee=s.fee, dorm_fee=s.dorm_fee,
        address=s.address, phone=s.phone, remark=s.remark,
        stats=[
            YearStat(year=st.year, plan=st.plan, min_score=st.min_score,
                     rank_city6=st.rank_city6, rank_whole=st.rank_whole)
            for st in stats
        ],
    )


@router.post("/schools", response_model=SchoolDetail, status_code=201)
def create_school(
    payload: SchoolCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """新增学校。校验 scope 合法、(code, scope) 唯一。"""
    if payload.scope not in (SCOPE_CITY6, SCOPE_WHOLE, SCOPE_SUBURB):
        raise HTTPException(400, f"非法招生口径: {payload.scope}")
    exists = (
        db.query(School)
        .filter(School.code == payload.code, School.scope == payload.scope)
        .first()
    )
    if exists:
        raise HTTPException(409, f"学校已存在: 代码 {payload.code} / {payload.scope}")
    school = School(**payload.model_dump())
    db.add(school)
    db.commit()
    db.refresh(school)
    return _school_to_detail(school)


@router.get("/schools", response_model=list[SchoolListItem])
def list_schools(
    scope: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """学校列表, 可按 scope 过滤、按名称/代码模糊搜索。"""
    query = db.query(School)
    if scope:
        query = query.filter(School.scope == scope)
    if q:
        like = f"%{q}%"
        query = query.filter((School.name.like(like)) | (School.code.like(like)))
    rows = query.order_by(School.code).all()
    return [
        SchoolListItem(
            id=s.id, code=s.code, name=s.name, scope=s.scope,
            type=s.type, location_district=s.location_district,
        )
        for s in rows
    ]


@router.get("/schools/{school_id}", response_model=SchoolDetail)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    s = db.get(School, school_id)
    if not s:
        raise HTTPException(404, "学校不存在")
    return _school_to_detail(s)


@router.put("/schools/{school_id}", response_model=SchoolDetail)
def update_school(
    school_id: int,
    payload: SchoolUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    s = db.get(School, school_id)
    if not s:
        raise HTTPException(404, "学校不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return _school_to_detail(s)


@router.delete("/schools/{school_id}")
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    s = db.get(School, school_id)
    if not s:
        raise HTTPException(404, "学校不存在")
    db.delete(s)  # cascade removes its stats
    db.commit()
    return {"deleted": school_id}


@router.put("/schools/{school_id}/stat", response_model=SchoolDetail)
def upsert_stat(
    school_id: int,
    payload: StatUpsert,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """新增或修改某校某年的录取数据(招生计划/最低分/位次)。"""
    s = db.get(School, school_id)
    if not s:
        raise HTTPException(404, "学校不存在")
    stat = (
        db.query(SchoolStat)
        .filter(SchoolStat.school_id == school_id, SchoolStat.year == payload.year)
        .first()
    )
    if stat is None:
        stat = SchoolStat(school_id=school_id, year=payload.year)
        db.add(stat)
    stat.plan = payload.plan
    stat.min_score = payload.min_score
    stat.rank_city6 = payload.rank_city6
    stat.rank_whole = payload.rank_whole
    db.commit()
    db.refresh(s)
    return _school_to_detail(s)


@router.delete("/schools/{school_id}/stat/{year}", response_model=SchoolDetail)
def delete_stat(
    school_id: int,
    year: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """删除某校某年的录取数据。"""
    s = db.get(School, school_id)
    if not s:
        raise HTTPException(404, "学校不存在")
    n = (
        db.query(SchoolStat)
        .filter(SchoolStat.school_id == school_id, SchoolStat.year == year)
        .delete()
    )
    if not n:
        raise HTTPException(404, f"该校无 {year} 年数据")
    db.commit()
    db.refresh(s)
    return _school_to_detail(s)


# ---------------- 一分档 CRUD ----------------
@router.get("/score-rank")
def list_score_rank(
    year: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    rows = (
        db.query(ScoreRank)
        .filter(ScoreRank.year == year)
        .order_by(ScoreRank.score.desc())
        .all()
    )
    return [
        {
            "id": r.id, "year": r.year, "score": r.score,
            "cum_whole": r.cum_whole, "cum_city6": r.cum_city6,
            "band_whole": r.band_whole, "band_city6": r.band_city6,
        }
        for r in rows
    ]


@router.put("/score-rank/{row_id}")
def update_score_rank(
    row_id: int,
    payload: ScoreRankUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    r = db.get(ScoreRank, row_id)
    if not r:
        raise HTTPException(404, "记录不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(r, field, value)
    db.commit()
    return {"updated": row_id}


@router.delete("/score-rank/{year}")
def delete_score_rank_year(
    year: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """删除某年整套一分档。"""
    n = db.query(ScoreRank).filter(ScoreRank.year == year).delete()
    db.commit()
    return {"deleted_year": year, "rows": n}


# ---------------- 阈值配置 ----------------
@router.get("/config")
def get_config(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """当前阈值(DB 覆盖 + 默认值补齐)。"""
    return matching.get_config(db)


@router.put("/config")
def update_config(
    payload: ConfigUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    allowed = set(matching.DEFAULT_CONFIG)
    for key, value in payload.values.items():
        if key not in allowed:
            raise HTTPException(400, f"未知配置项: {key}")
        row = db.get(AppConfig, key)
        if row is None:
            db.add(AppConfig(key=key, value=str(value)))
        else:
            row.value = str(value)
    db.commit()
    return matching.get_config(db)
