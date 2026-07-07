"""대시보드 배포용 데이터 스냅샷 — fomc.db 의 필요한 테이블을 CSV로 내보낸다.

클라우드(Streamlit Community Cloud)엔 data/fomc.db·모델이 없으므로, 이 CSV들을
커밋해두면 dashboard/data.py 가 폴백으로 읽어 대시보드가 동작한다.
값은 숫자·문장 텍스트뿐 — 비밀 없음.

실행(로컬, DB 있을 때):  python dashboard/export_snapshot.py
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "fomc.db"
OUT = Path(__file__).resolve().parent / "snapshot"

TABLES = {
    "meetings": "SELECT date, method, granularity, index_value, confidence FROM meetings",
    "market": "SELECT date, spx_close, spx_ret_cc, vix, vix_chg, ust2y, ust10y FROM market",
    "macro": "SELECT date, series, value FROM macro",
    "sentences": ("SELECT date, sentence_idx, sentence, p_pos, p_neu, p_neg, "
                  "score, entropy, model_tag FROM sentences"),
}


def main():
    import pandas as pd
    if not DB.exists():
        print(f"[오류] {DB} 없음. pipeline·collect_market·collect_macro 후 실행하세요.")
        return
    OUT.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    for name, q in TABLES.items():
        try:
            df = pd.read_sql_query(q, con)
            df.to_csv(OUT / f"{name}.csv", index=False)
            print(f"  {name}: {len(df)}행 → snapshot/{name}.csv")
        except Exception as e:
            print(f"  {name}: 건너뜀 — {str(e)[:50]}")
    con.close()

    # 실행 로그(운영 페이지용)도 스냅샷으로
    try:
        from agents.runlog import read_runs
        runs = read_runs()
        if runs:
            pd.DataFrame(runs).to_csv(OUT / "runs.csv", index=False)
            print(f"  runs: {len(runs)}행 → snapshot/runs.csv")
    except Exception as e:
        print(f"  runs: 건너뜀 — {str(e)[:50]}")
    print(f"\n완료 → {OUT}")


if __name__ == "__main__":
    main()
