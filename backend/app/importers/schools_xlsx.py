"""高中数据 importer: three sheets -> school (static) + school_stat (yearly long rows).

The workbook has three sheets, mapped to recruitment scopes:
    面向市内六区招生 -> city6   (has 市区位次 + 全市位次 per year, plus 食堂/班型)
    面向全市招生     -> whole   (only 全市位次, has 食堂/班型)
    面向郊区招生     -> suburb  (only 全市位次, NO 食堂/班型)

Columns differ between sheets, so we map by NORMALIZED header name
(newlines/spaces stripped) instead of fixed indices. Each year's wide columns
(招生计划/录取最低分/位次 for 2022..2025) are un-pivoted into school_stat rows.

A full import replaces ALL schools + stats (latest workbook wins).
"""
import re
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from ..models import SCOPE_CITY6, SCOPE_SUBURB, SCOPE_WHOLE, School, SchoolStat

SHEET_SCOPE = {
    "面向市内六区招生": SCOPE_CITY6,
    "面向全市招生": SCOPE_WHOLE,
    "面向郊区招生": SCOPE_SUBURB,
}

YEARS = [2025, 2024, 2023, 2022]


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
    """Parse all three sheets into a flat list of school dicts.

    Each dict has static fields plus a "stats" list of yearly rows.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    schools: list[dict] = []

    for ws in wb.worksheets:
        scope = SHEET_SCOPE.get(ws.title)
        if scope is None:
            continue  # unknown sheet — skip

        rows = list(ws.iter_rows(values_only=True))
        header = rows[0]
        col = {_norm(h): i for i, h in enumerate(header)}

        def cell(row, name):
            i = col.get(name)
            return row[i] if i is not None and i < len(row) else None

        for row in rows[1:]:
            code = _to_str(cell(row, "代码"))
            name = _to_str(cell(row, "学校"))
            if not code or not name:
                continue  # blank / separator row

            stats = []
            for y in YEARS:
                stats.append(
                    {
                        "year": y,
                        "plan": _to_int(cell(row, f"{y}年招生计划")),
                        "min_score": _to_float(cell(row, f"{y}年录取最低分")),
                        "rank_city6": _to_int(cell(row, f"{y}年市区录取位次")),
                        "rank_whole": _to_int(cell(row, f"{y}年全市录取位次")),
                    }
                )

            schools.append(
                {
                    "code": code,
                    "scope": scope,
                    "name": name,
                    "home_district": _to_str(cell(row, "归属区")),
                    "location_district": _to_str(cell(row, "所在区")),
                    "recruit_area": _to_str(cell(row, "招生区域")),
                    "type": _to_str(cell(row, "类型")),
                    "boarding": _to_str(cell(row, "住宿")),
                    "canteen": _to_str(cell(row, "食堂")),       # 郊区表无 -> None
                    "class_types": _to_str(cell(row, "班型")),   # 郊区表无 -> None
                    "fee": _to_str(cell(row, "学费（学年）")),
                    "dorm_fee": _to_str(cell(row, "住宿费")),
                    "address": _to_str(cell(row, "学校地址")),
                    "phone": _to_str(cell(row, "咨询电话")),
                    "remark": _to_str(cell(row, "备注")),
                    "stats": stats,
                }
            )
    return schools


def import_schools(db: Session, path: str | Path) -> dict[str, int]:
    """Import schools xlsx, replacing all school + school_stat rows.

    Returns counts per scope plus totals.
    """
    parsed = parse_schools(path)

    # Full replace (cascade deletes stats).
    db.query(SchoolStat).delete()
    db.query(School).delete()

    counts = {SCOPE_CITY6: 0, SCOPE_WHOLE: 0, SCOPE_SUBURB: 0}
    stat_rows = 0
    for s in parsed:
        stats = s.pop("stats")
        school = School(**s)
        # keep only stat rows that carry at least one real value
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
