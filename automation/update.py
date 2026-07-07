"""전체 갱신 + 클라우드 발행 — 원커맨드 (1-b).

로컬 데이터 갱신(agents/refresh.py) → 클라우드 발행(dashboard/publish.py)을
한 번에 실행해 로컬·Streamlit Cloud 대시보드를 모두 최신화한다.

실행:
  SENTIMENT_ENGINE=finbert python update.py           # 새 회의만 → 갱신+발행
  SENTIMENT_ENGINE=finbert python update.py --all     # 전체 재처리 → 갱신+발행
  python update.py --no-publish                       # 로컬만(발행 생략)
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(script: str, *args) -> int:
    env = {**os.environ, "PYTHONUTF8": "1"}
    env.setdefault("SENTIMENT_ENGINE", "finbert")
    return subprocess.run([sys.executable, str(ROOT / script), *args],
                          cwd=str(ROOT), env=env).returncode


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    refresh_args = ["--all"] if "--all" in args else []

    print("=" * 44)
    print("[1/2] 로컬 갱신 — 감성 · 시장 · 거시")
    print("=" * 44)
    _run("agents/refresh.py", *refresh_args)

    if "--no-publish" in args:
        print("\n(발행 생략 — 로컬만 갱신)")
        return

    print("\n" + "=" * 44)
    print("[2/2] 클라우드 발행 — 스냅샷 push")
    print("=" * 44)
    _run("dashboard/publish.py")

    print("\n✅ 전체 완료 — 로컬 + 클라우드 대시보드 최신화.")


if __name__ == "__main__":
    main()
