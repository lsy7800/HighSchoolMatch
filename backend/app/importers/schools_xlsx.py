"""高中数据 importer: 单 sheet -> school (静态) + school_stat (逐年 long rows)。

数据源: data_source/2026年天津高中信息调查表.xlsx
- 单 sheet, 每行一所学校(一个 招生范围=scope)。
- 2025/2024 两年的招生人数/最低分/位次 以宽列展开, 这里 un-pivot 成
  school_stat 的逐年行(只保留至少有一个值的年份)。
- 学校简介(intro)不从 xlsx 导入: 导入时按 (code, scope) 快照已有 intro,
  全量替换后回填, 避免覆盖手动补全的内容。

全量替换: latest workbook wins。
"""
import re
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from ..models import SCOPE_CITY6, SCOPE_SUBURB, SCOPE_WHOLE, School, SchoolStat

# 招生范围文本 -> scope 代码
SCOPE_TEXT = {
    "市内六区": SCOPE_CITY6,
    "全市": SCOPE_WHOLE,
    "郊区": SCOPE_SUBURB,
}

# 多年宽列(招生人数/录取最低分/六区录取位次/全市录取位次)
# 2026 仅含招生人数; 2025/2024 含全部字段。缺字段的年份仍可入表(按非空保留)。
YEARS = [2026, 2025, 2024]


def _norm(h) -> str:
    """Normalize a header cell: drop newlines/whitespace."""
    if h is None:
        return ""
    return re.sub(r"\s+", "", str(h))


def _to_int(v):
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _to_str(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def parse_schools(path: str | Path) -> list[dict]:
    """解析单 sheet 为学校 dict 列表(含 stats 逐年行)。"""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]  # 单 sheet
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = rows[0]
    col = {_norm(h): i for i, h in enumerate(header)}

    def cell(row, name):
        i = col.get(name)
        return row[i] if i is not None and i < len(row) else None

    schools: list[dict] = []
    for row in rows[1:]:
        code = _to_str(cell(row, "学校代码"))
        name = _to_str(cell(row, "学校名称"))
        if not code or not name:
            continue  # 空行/分隔行
        scope = SCOPE_TEXT.get(_to_str(cell(row, "招生范围")) or "")
        if scope is None:
            continue  # 未知招生范围, 跳过

        stats = []
        for y in YEARS:
            stats.append(
                {
                    "year": y,
                    "plan": _to_int(cell(row, f"{y}年招生人数")),
                    "min_score": _to_float(cell(row, f"{y}年录取最低分")),
                    "rank_city6": _to_int(cell(row, f"{y}年六区录取位次")),
                    "rank_whole": _to_int(cell(row, f"{y}年全市录取位次")),
                }
            )

        schools.append(
            {
                "code": code,
                "scope": scope,
                "name": name,
                "type": _to_str(cell(row, "类型")),
                "location_district": _to_str(cell(row, "所在区域")),
                "boarding": _to_str(cell(row, "住宿")),
                "canteen": _to_str(cell(row, "餐饮")),
                "class_types": _to_str(cell(row, "班型设置")),
                "subject_model": _to_str(cell(row, "选科模式")),
                "class_adjust": _to_str(cell(row, "调班机制")),
                "schedule": _to_str(cell(row, "作息")),
                "fee": _to_str(cell(row, "学费")),
                "fee_reduction": _to_str(cell(row, "学费减免")),
                "remark": _to_str(cell(row, "备注")),
                "other_info": _to_str(cell(row, "其他情况")),
                "stats": stats,
            }
        )
    return schools


def import_schools(db: Session, path: str | Path) -> dict[str, int]:
    """全量替换 school + school_stat, 保留已有 intro(按 code+scope 快照回填)。

    Returns counts per scope plus totals.
    """
    parsed = parse_schools(path)

    # 快照现有 intro(手动补全的, 不能被全量替换冲掉)
    intro_map = {
        (s.code, s.scope): s.intro
        for s in db.query(School).filter(School.intro.isnot(None)).all()
    }

    # Full replace (cascade deletes stats).
    db.query(SchoolStat).delete()
    db.query(School).delete()

    counts = {SCOPE_CITY6: 0, SCOPE_WHOLE: 0, SCOPE_SUBURB: 0}
    stat_rows = 0
    for s in parsed:
        stats = s.pop("stats")
        s["intro"] = intro_map.get((s["code"], s["scope"]))  # 回填已有简介
        school = School(**s)
        # 只保留至少有一个真实值的年份
        for st in stats:
            if any(v is not None for k, v in st.items() if k != "year"):
                school.stats.append(SchoolStat(**st))
                stat_rows += 1
        db.add(school)
        counts[s["scope"]] += 1
    db.commit()

    counts["schools_total"] = sum(
        counts[k] for k in (SCOPE_CITY6, SCOPE_WHOLE, SCOPE_SUBURB)
    )
    counts["stat_rows"] = stat_rows
    return counts
