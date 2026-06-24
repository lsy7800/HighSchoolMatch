"""Public (student-facing) API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from .. import matching
from ..database import get_db
from ..models import School, ScoreRank
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
                home_district=s.home_district, location_district=s.location_district,
                recruit_area=s.recruit_area, boarding=s.boarding, canteen=s.canteen,
                class_types=s.class_types, fee=s.fee, dorm_fee=s.dorm_fee,
                address=s.address, phone=s.phone, remark=s.remark,
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
