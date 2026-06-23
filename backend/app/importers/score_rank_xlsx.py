"""一分档 importer: reads the score-rank xlsx into the score_rank table.

Source columns (Sheet1):
  exam_year | score_range | city_sum | districts_sum | city_even | districts_even

city_sum / districts_sum are cumulative counts (位次).
city_even / districts_even are per-band counts but stored as Excel FORMULAS
(=C3-C2 ...), so we ignore them and recompute the band ourselves from the
cumulative columns — robust and formula-independent.

Replaces all rows for each year present in the file (year-versioned).
"""
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from ..models import ScoreRank


def parse_score_rank(path: str | Path) -> dict[int, list[dict]]:
    """Parse the xlsx into {year: [row dicts sorted by score desc]}.

    band = people scoring exactly this score = cum[score] - cum[score+1].
    For the top score (no score above it) band == cum.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    ws = wb.active

    rows = list(ws.iter_rows(min_row=2, values_only=True))  # skip header
    # Group raw (year, score, cum_whole, cum_city6) by year.
    by_year: dict[int, list[tuple]] = {}
    for r in rows:
        if r is None or r[0] is None or r[1] is None:
            continue
        year = int(r[0])
        score = int(r[1])
        cum_whole = int(r[2])
        cum_city6 = int(r[3])
        by_year.setdefault(year, []).append((score, cum_whole, cum_city6))

    result: dict[int, list[dict]] = {}
    for year, items in by_year.items():
        # Sort by score descending (highest score first / smallest cumulative).
        items.sort(key=lambda x: -x[0])
        out = []
        for i, (score, cum_whole, cum_city6) in enumerate(items):
            if i == 0:
                band_whole, band_city6 = cum_whole, cum_city6
            else:
                prev = items[i - 1]  # next-higher score
                band_whole = cum_whole - prev[1]
                band_city6 = cum_city6 - prev[2]
            out.append(
                {
                    "year": year,
                    "score": score,
                    "cum_whole": cum_whole,
                    "cum_city6": cum_city6,
                    "band_whole": band_whole,
                    "band_city6": band_city6,
                }
            )
        result[year] = out
    return result


def import_score_rank(db: Session, path: str | Path) -> dict[int, int]:
    """Import score-rank xlsx into DB, replacing each year's rows.

    Returns {year: row_count}.
    """
    parsed = parse_score_rank(path)
    counts: dict[int, int] = {}
    for year, rows in parsed.items():
        db.query(ScoreRank).filter(ScoreRank.year == year).delete()
        db.add_all([ScoreRank(**row) for row in rows])
        counts[year] = len(rows)
    db.commit()
    return counts
