"""One-shot seed: load 2025 一分档 + 高中数据 into a fresh SQLite DB.

Run from backend/:  python -m scripts.seed_2025
"""
import sys
from pathlib import Path

# allow `from app...` when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db  # noqa: E402
from app.importers.schools_xlsx import import_schools  # noqa: E402
from app.importers.score_rank_xlsx import import_score_rank  # noqa: E402

DATA = Path(__file__).resolve().parent.parent.parent / "data_source"
SCORE_RANK_XLSX = DATA / "2025年一分档.xlsx"
SCHOOLS_XLSX = DATA / "天津市高中数据汇总2025（分区）.xlsx"


def main():
    init_db()
    db = SessionLocal()
    try:
        print("Importing 一分档 ...")
        sr = import_score_rank(db, SCORE_RANK_XLSX)
        for year, n in sr.items():
            print(f"  year {year}: {n} score bands")

        print("Importing 高中数据 ...")
        sc = import_schools(db, SCHOOLS_XLSX)
        print(
            f"  city6={sc['city6']} whole={sc['whole']} suburb={sc['suburb']} "
            f"total={sc['schools_total']} stat_rows={sc['stat_rows']}"
        )

        # --- validation ---
        problems = []
        if sr.get(2025) != 281:
            problems.append(f"expected 281 score bands for 2025, got {sr.get(2025)}")
        if sc["city6"] != 81:
            problems.append(f"expected 81 city6 schools, got {sc['city6']}")
        if sc["whole"] != 48:
            problems.append(f"expected 48 whole schools, got {sc['whole']}")
        if sc["suburb"] != 149:
            problems.append(f"expected 149 suburb schools, got {sc['suburb']}")

        if problems:
            print("\nVALIDATION FAILED:")
            for p in problems:
                print("  -", p)
            sys.exit(1)
        print("\nValidation OK — seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
