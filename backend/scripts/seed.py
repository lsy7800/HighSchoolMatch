"""One-shot seed: load 一分档 + 高中数据 into a fresh SQLite DB.

Run from backend/:  python -m scripts.seed
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
SCHOOLS_XLSX = DATA / "2026年天津高中信息调查表.xlsx"


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
        # 一分档精确校验(稳定); 学校数只做下限合理性校验(数据源可能增减几所,
        # 且个别行若缺学校代码会被跳过——见导入器日志)。
        problems = []
        if sr.get(2025) != 281:
            problems.append(f"expected 281 score bands for 2025, got {sr.get(2025)}")
        if sc["schools_total"] < 100:
            problems.append(f"expected >=100 schools, got {sc['schools_total']}")
        if sc["city6"] < 80:
            problems.append(f"expected >=80 city6 schools, got {sc['city6']}")
        if sc["whole"] < 40:
            problems.append(f"expected >=40 whole schools, got {sc['whole']}")

        if problems:
            print("\nVALIDATION FAILED:")
            for p in problems:
                print("  -", p)
            sys.exit(1)
        print(f"\nValidation OK — seed complete. (city6={sc['city6']} whole={sc['whole']} total={sc['schools_total']})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
