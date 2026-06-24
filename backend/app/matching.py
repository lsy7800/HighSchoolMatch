"""匹配引擎: 位次换算 + 等位分 + 冲/稳/保 分类.

核心约定(位次法):
  一分档里 "X分以上的累计人数" == 处于该分数位置的位次(rank).
  学校的"录取位次"恰好就是其"录取最低分(向下取整档)"对应的累计人数。
  例: 天津一中 2025 录取最低分 768.9 -> 768档 市内六区累计 1193 == 其市区录取位次。

匹配方向(位次数值越小越靠前):
  学校录取到位次 N(录取位次). 学生位次 <= N 即达线, 越小越稳。
  ratio = 学生位次 / 学校录取位次
    ratio <  1 - margin   -> 保 (明显达线)
    1-margin..1+margin    -> 稳 (临界)
    ratio >  1 + margin   -> 冲 (未达线, 够一够)
所有阈值存 app_config, 后台可调。
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .models import (
    SCOPE_CITY6,
    SCOPE_WHOLE,
    AppConfig,
    School,
    SchoolStat,
    ScoreRank,
)

# ---- 默认可配置阈值(写入 app_config 后以 DB 为准) ----
DEFAULT_CONFIG = {
    "stable_margin": 0.10,   # 稳: 位次比在 ±10% 内
    "safe_floor": 0.5,       # 保: ratio 低于此值(过度超线)的学校不再推荐
    "reach_ceiling": 1.5,    # 冲: ratio 高于此值(差距过大)的学校不再推荐
}

CATEGORY_SAFE = "safe"     # 保
CATEGORY_STABLE = "stable"  # 稳
CATEGORY_REACH = "reach"   # 冲


def get_config(db: Session) -> dict[str, float]:
    """读取阈值配置, 缺失项用默认值补齐。"""
    cfg = dict(DEFAULT_CONFIG)
    for row in db.query(AppConfig).all():
        if row.key in cfg:
            try:
                cfg[row.key] = float(row.value)
            except (ValueError, TypeError):
                pass
    return cfg


@dataclass
class RankResult:
    score: float          # 原始输入分
    floor_score: int      # 向下取整后的查表分
    rank_whole: int       # 全市位次
    rank_city6: int       # 市内六区位次
    out_of_range: bool    # 是否超出一分档范围(已夹取边界)
    below_floor: bool     # 是否低于最低档(分数过低, 触发"能上哪所上哪所"模式)


def _load_bands(db: Session, year: int) -> list[ScoreRank]:
    """按分数降序返回某年一分档(高分在前)。"""
    return (
        db.query(ScoreRank)
        .filter(ScoreRank.year == year)
        .order_by(ScoreRank.score.desc())
        .all()
    )


def score_to_rank(db: Session, score: float, year: int) -> RankResult | None:
    """分数 -> (全市位次, 市内六区位次)。

    小数分向下取整到整数档(如 768.9 -> 768)。
    超出范围则夹取到最高/最低档并置 out_of_range。
    """
    bands = _load_bands(db, year)
    if not bands:
        return None

    top, bottom = bands[0], bands[-1]  # top=最高分, bottom=最低分
    floor_score = int(score // 1)
    out = False
    below = False

    if floor_score >= top.score:
        b = top
        out = floor_score > top.score
    elif floor_score <= bottom.score:
        b = bottom
        out = floor_score < bottom.score
        below = floor_score < bottom.score  # 严格低于最低档 -> 低分模式
    else:
        # 找到 score 恰好等于 floor_score 的档(一分档为连续整数, 必命中)
        b = next((x for x in bands if x.score == floor_score), None)
        if b is None:
            # 兜底: 取不高于 floor_score 的最高档
            b = next((x for x in bands if x.score <= floor_score), bottom)

    return RankResult(
        score=score,
        floor_score=floor_score,
        rank_whole=b.cum_whole,
        rank_city6=b.cum_city6,
        out_of_range=out,
        below_floor=below,
    )


def rank_to_equiv_score(
    db: Session, rank: int, year: int, scope_whole: bool
) -> int | None:
    """位次 -> 等位分(该年一分档中对应的分数)。

    用于跨年等位: 2026位次 + 2025一分档 -> 2025等位分, 与学校2025最低分可比。
    scope_whole=True 用全市累计列, 否则用市内六区累计列。
    返回累计人数首次 >= rank 的最高分。
    """
    bands = _load_bands(db, year)  # 高分在前
    if not bands:
        return None
    for b in bands:
        cum = b.cum_whole if scope_whole else b.cum_city6
        if cum >= rank:
            return b.score
    return bands[-1].score  # rank 超过总人数 -> 最低分


def classify(student_rank: int, school_rank: int, cfg: dict[str, float]) -> str | None:
    """按 ratio = 学生位次/学校录取位次 分类, 越界返回 None(不推荐)。"""
    if not school_rank:
        return None
    ratio = student_rank / school_rank
    m = cfg["stable_margin"]
    if ratio < 1 - m:
        return None if ratio < cfg["safe_floor"] else CATEGORY_SAFE
    if ratio <= 1 + m:
        return CATEGORY_STABLE
    return None if ratio > cfg["reach_ceiling"] else CATEGORY_REACH


def _student_rank_for_scope(rank: RankResult, scope: str) -> int:
    """市内六区学校用市区位次, 全市/郊区学校用全市位次。"""
    return rank.rank_city6 if scope == SCOPE_CITY6 else rank.rank_whole


def _school_entry(s, stat, school_rank, student_rank) -> dict:
    return {
        "code": s.code,
        "name": s.name,
        "scope": s.scope,
        "type": s.type,
        "location_district": s.location_district,
        "boarding": s.boarding,
        "class_types": s.class_types,
        "school_rank": school_rank,
        "student_rank": student_rank,
        "min_score": stat.min_score,
        "plan": stat.plan,
        "ratio": round(student_rank / school_rank, 4) if school_rank else None,
    }


def _iter_school_stats(db: Session, ref_year: int):
    """逐校产出 (school, stat, school_rank), 跳过无数据/无位次的。

    只面向市内六区考生: 仅可填报「市内六区招生」「全市招生」的学校,
    「郊区招生」(SCOPE_SUBURB)学校市内六区考生不能填报, 直接排除。
    """
    schools = (
        db.query(School)
        .filter(School.scope.in_([SCOPE_CITY6, SCOPE_WHOLE]))
        .all()
    )
    for s in schools:
        stat = (
            db.query(SchoolStat)
            .filter(SchoolStat.school_id == s.id, SchoolStat.year == ref_year)
            .first()
        )
        if stat is None:
            continue
        school_rank = stat.rank_city6 if s.scope == SCOPE_CITY6 else stat.rank_whole
        if not school_rank:
            continue
        yield s, stat, school_rank


def recommend(
    db: Session, score: float, year: int, ref_year: int | None = None
) -> dict:
    """主流程: 分数 -> 位次/等位分 -> 各校冲稳保分类。

    year:     用于把分数换算成位次的一分档年份(今年)。
    ref_year: 用于"等位分"和学校录取数据比对的年份(默认同 year)。
              2026 上线后传 year=2026, ref_year=2025。

    低分模式: 当分数低于一分档最低档(below_floor)时, 冲/稳/保 已无意义,
    改为返回单一 reachable 列表(所有学校按录取门槛从低到高排序,
    "能上哪所上哪所"), 并置 low_score_mode=True。
    """
    ref_year = ref_year or year
    cfg = get_config(db)

    rank = score_to_rank(db, score, year)
    if rank is None:
        return {"error": f"no score-rank data for year {year}"}

    # 等位分: 用今年位次反查 ref_year 一分档
    equiv_whole = rank_to_equiv_score(db, rank.rank_whole, ref_year, scope_whole=True)
    equiv_city6 = rank_to_equiv_score(db, rank.rank_city6, ref_year, scope_whole=False)

    base = {
        "score": score,
        "year": year,
        "ref_year": ref_year,
        "rank_whole": rank.rank_whole,
        "rank_city6": rank.rank_city6,
        "equiv_score_whole": equiv_whole,
        "equiv_score_city6": equiv_city6,
        "out_of_range": rank.out_of_range,
        "low_score_mode": rank.below_floor,
        "config": cfg,
    }

    # ---- 低分模式: 不分冲稳保, 列出所有学校(门槛从低到高) ----
    if rank.below_floor:
        reachable = []
        for s, stat, school_rank in _iter_school_stats(db, ref_year):
            student_rank = _student_rank_for_scope(rank, s.scope)
            reachable.append(_school_entry(s, stat, school_rank, student_rank))
        # 录取位次越大=门槛越低=越容易上, 放最前
        reachable.sort(key=lambda x: -x["school_rank"])
        return {
            **base,
            "reachable": reachable,
            "reach": [],
            "stable": [],
            "safe": [],
        }

    # ---- 正常模式: 冲/稳/保 ----
    buckets = {CATEGORY_REACH: [], CATEGORY_STABLE: [], CATEGORY_SAFE: []}
    for s, stat, school_rank in _iter_school_stats(db, ref_year):
        student_rank = _student_rank_for_scope(rank, s.scope)
        cat = classify(student_rank, school_rank, cfg)
        if cat is None:
            continue
        buckets[cat].append(_school_entry(s, stat, school_rank, student_rank))

    # 每组按 ratio 升序(越接近达线越靠前)
    for items in buckets.values():
        items.sort(key=lambda x: x["ratio"])

    return {
        **base,
        "reachable": [],
        "reach": buckets[CATEGORY_REACH],
        "stable": buckets[CATEGORY_STABLE],
        "safe": buckets[CATEGORY_SAFE],
    }
