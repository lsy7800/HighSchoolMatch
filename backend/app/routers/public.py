"""Public (student-facing) API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from .. import chat, matching
from ..database import SessionLocal, get_db
from ..models import School, SchoolStat, ScoreRank
from ..schemas import RecommendRequest, RecommendResponse, SchoolDetail, YearStat

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/years")
def list_years(db: Session = Depends(get_db)) -> list[int]:
    """一分档可用年份(降序)。"""
    rows = db.query(distinct(ScoreRank.year)).order_by(ScoreRank.year.desc()).all()
    return [r[0] for r in rows]


def _latest_year(db: Session) -> int | None:
    row = db.query(ScoreRank.year).order_by(ScoreRank.year.desc()).first()
    return row[0] if row else None


@router.get("/score-rank")
def score_rank_table(year: int | None = None, db: Session = Depends(get_db)):
    """某年一分一段表(分数降序), 供学生查看。默认最新年份。"""
    year = year or _latest_year(db)
    if year is None:
        raise HTTPException(404, "无一分档数据")
    rows = (
        db.query(ScoreRank)
        .filter(ScoreRank.year == year)
        .order_by(ScoreRank.score.desc())
        .all()
    )
    return {
        "year": year,
        "rows": [
            {
                "score": r.score,
                "cum_whole": r.cum_whole,
                "cum_city6": r.cum_city6,
                "band_whole": r.band_whole,
                "band_city6": r.band_city6,
            }
            for r in rows
        ],
    }


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    year = req.year or _latest_year(db)
    if year is None:
        raise HTTPException(404, "无一分档数据, 请先在后台导入。")
    result = matching.recommend(db, req.score, year, req.ref_year)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/districts")
def list_districts(db: Session = Depends(get_db)):
    """所有学校出现过的所在区(去重升序)，供筛选下拉。"""
    rows = db.query(distinct(School.location_district)).order_by(School.location_district).all()
    return [r[0] for r in rows if r[0]]


@router.get("/schools")
def list_schools(
    q: str | None = Query(None, description="名称/代码模糊搜索"),
    scope: str | None = Query(None, description="city6/whole/suburb"),
    type: str | None = Query(None, description="公办/民办"),
    district: str | None = Query(None, description="所在区精确匹配"),
    db: Session = Depends(get_db),
):
    """学校列表，含最新一年录取数据摘要，供公开浏览页使用。"""
    qs = db.query(School)
    if q:
        like = f"%{q}%"
        qs = qs.filter((School.name.like(like)) | (School.code.like(like)))
    if scope:
        qs = qs.filter(School.scope == scope)
    if type:
        qs = qs.filter(School.type == type)
    if district:
        qs = qs.filter(School.location_district == district)
    schools = qs.order_by(School.code).all()

    # 最新一年的 min_score / rank_city6 / rank_whole（子查询）
    latest_year_sub = (
        db.query(SchoolStat.school_id, func.max(SchoolStat.year).label("max_year"))
        .group_by(SchoolStat.school_id)
        .subquery()
    )
    stat_rows = (
        db.query(SchoolStat)
        .join(
            latest_year_sub,
            (SchoolStat.school_id == latest_year_sub.c.school_id)
            & (SchoolStat.year == latest_year_sub.c.max_year),
        )
        .all()
    )
    stat_map = {st.school_id: st for st in stat_rows}

    result = []
    for s in schools:
        st = stat_map.get(s.id)
        result.append(
            {
                "code": s.code,
                "name": s.name,
                "scope": s.scope,
                "type": s.type,
                "location_district": s.location_district,
                "boarding": s.boarding,
                "canteen": s.canteen,
                "class_types": s.class_types,
                "intro": (s.intro or "")[:80] + ("…" if s.intro and len(s.intro) > 80 else ""),
                "latest_year": st.year if st else None,
                "latest_min_score": st.min_score if st else None,
                "latest_rank_city6": st.rank_city6 if st else None,
                "latest_rank_whole": st.rank_whole if st else None,
            }
        )
    return result


@router.get("/schools/{code}", response_model=list[SchoolDetail])
def school_detail(code: str, db: Session = Depends(get_db)):
    """按代码返回学校(可能含全市+郊区两条招生线)。"""
    schools = db.query(School).filter(School.code == code).all()
    if not schools:
        raise HTTPException(404, f"未找到学校代码 {code}")
    out = []
    for s in schools:
        stats = sorted(s.stats, key=lambda x: x.year, reverse=True)
        out.append(
            SchoolDetail(
                code=s.code, name=s.name, scope=s.scope, type=s.type,
                location_district=s.location_district,
                boarding=s.boarding, canteen=s.canteen, class_types=s.class_types,
                subject_model=s.subject_model, class_adjust=s.class_adjust,
                schedule=s.schedule, fee=s.fee, fee_reduction=s.fee_reduction,
                remark=s.remark, other_info=s.other_info, intro=s.intro,
                stats=[
                    YearStat(
                        year=st.year, plan=st.plan, min_score=st.min_score,
                        rank_city6=st.rank_city6, rank_whole=st.rank_whole,
                    )
                    for st in stats
                ],
            )
        )
    return out


# ---------------- 智能问答 ----------------
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: "..."}]


@router.post("/chat")
def chat_endpoint(req: ChatRequest, request: Request):
    """智能问答(SSE 流式)。无登录, 简单按 IP 限流。"""
    ip = request.client.host if request.client else "unknown"
    if not chat.check_rate(ip):
        raise HTTPException(429, "提问太频繁，请稍后再试")

    message = (req.message or "").strip()
    if not message:
        raise HTTPException(400, "消息不能为空")
    if len(message) > 500:
        raise HTTPException(400, "消息过长（上限 500 字）")

    # 流式生成器自带 db session(独立于请求生命周期, 在生成器结束时关闭)
    def gen():
        db = SessionLocal()
        try:
            yield from chat.stream_chat(message, req.history, db)
        finally:
            db.close()

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 让 nginx 不缓冲, SSE 实时下发
        },
    )
