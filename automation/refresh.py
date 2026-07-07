"""데이터 갱신 에이전트 (오케스트레이터) — 대시보드용.

수동이던 갱신 절차(감성→시장→거시)를 한 번에 실행하는 '갱신 에이전트'.
검증된 함수(pipeline.run · collect_market · collect_macro)를 순서대로 조율하고
각 단계 성공/실패를 로그로 남긴다(한 단계 실패해도 계속). 대시보드가 읽는
data/fomc.db 에 직접 쓰므로, 실행 후 캐시만 비우면 화면이 갱신된다.

원칙(Phase 6~7): 로직은 검증된 함수에, 조율만 여기서. 새 분석 로직 없음.

실행:
  SENTIMENT_ENGINE=finbert python agents/refresh.py          # 새 회의만(빠름)
  SENTIMENT_ENGINE=finbert python agents/refresh.py --all    # 전체 재처리
"""
import glob
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "fomc.db"
CORPUS_DIRS = [ROOT / "data" / "statements", ROOT / "tests" / "fixtures"]


def discover_statements() -> dict:
    """{날짜: 파일경로} — 코퍼스의 성명문 (data/statements 우선, fixtures 보조)."""
    found = {}
    for d in CORPUS_DIRS:
        for f in sorted(glob.glob(str(d / "FOMC_*.txt"))):
            m = re.search(r"(\d{4}-\d{2}-\d{2})", Path(f).name)
            if m and m.group(1) not in found:
                found[m.group(1)] = f
    return found


def existing_dates(db=None) -> set:
    """이미 fomc.db 에 감성분석된 회의 날짜들."""
    db = Path(db) if db is not None else DB
    if not db.exists():
        return set()
    con = sqlite3.connect(str(db))
    try:
        rows = con.execute("SELECT DISTINCT date FROM meetings").fetchall()
    except sqlite3.OperationalError:
        rows = []
    con.close()
    return {r[0] for r in rows}


def pending_dates(new_only: bool = True) -> list:
    """처리할 회의 날짜 목록 (new_only 면 아직 DB에 없는 것만)."""
    stmts = discover_statements()
    dates = sorted(stmts)
    if new_only:
        have = existing_dates()
        dates = [d for d in dates if d not in have]
    return dates


def run(new_only: bool = True, log=print) -> dict:
    """감성 → 시장 → 거시 순으로 fomc.db 를 갱신. 결과 요약 dict 반환."""
    stmts = discover_statements()
    todo = pending_dates(new_only)
    log(f"[1/3 감성] 대상 {len(todo)}건 " + ("(새 회의)" if new_only else "(전체)"))

    ok = 0
    if todo:
        import pipeline  # engine 은 SENTIMENT_ENGINE 에 따라 로드
        for date in todo:
            try:
                pipeline.run(Path(stmts[date]), date)
                ok += 1
                log(f"    [OK] {date}")
            except Exception as e:
                log(f"    [실패] {date}: {str(e)[:50]}")
    log(f"[1/3 감성] 완료 {ok}/{len(todo)}")

    market_ok = _step(log, "2/3 시장", "analysis.collect_market")
    macro_ok = _step(log, "3/3 거시", "analysis.collect_macro")

    log("✅ 갱신 완료.")
    return {"processed": ok, "attempted": len(todo),
            "market_ok": market_ok, "macro_ok": macro_ok}


def _step(log, tag: str, module: str) -> bool:
    """수집 모듈의 main() 을 호출하고 성공 여부를 로그."""
    try:
        import importlib
        importlib.import_module(module).main()
        log(f"[{tag}] 완료")
        return True
    except Exception as e:
        log(f"[{tag}] 실패: {str(e)[:70]}")
        return False


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    new_only = "--all" not in sys.argv[1:]
    run(new_only=new_only)


if __name__ == "__main__":
    main()
