"""대시보드 발행 에이전트 — 로컬 최신 데이터를 개인 배포 레포로 push.

로컬 fomc.db 를 스냅샷(CSV)으로 내보내고, 대시보드 코드와 함께 배포 레포로
동기화한 뒤 git push 한다. → Streamlit Cloud 가 자동 재배포(공개 URL 갱신).

이걸로 '전체 갱신(agents/refresh.py) → 발행(이 스크립트)' 두 단계면
로컬·클라우드 대시보드가 모두 최신이 된다.

배포 폴더: 환경변수 DEPLOY_DIR (기본 아래 경로)
실행:  python dashboard/publish.py
       python dashboard/publish.py -m "커밋 메시지"
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = Path(os.getenv("DEPLOY_DIR", r"C:\Users\USER\fomc-dashboard-deploy"))

# 배포 레포에 둘 최소 모듈 (대시보드 실행에 필요한 것만)
ANALYSIS = ["__init__.py", "signals.py", "backtest.py", "analyze_alignment.py"]
AGENTS = ["__init__.py", "runlog.py"]


def _run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def export_snapshot():
    """fomc.db → dashboard/snapshot/*.csv (배포용)."""
    r = _run(sys.executable, str(ROOT / "dashboard" / "export_snapshot.py"), cwd=str(ROOT))
    print(r.stdout.strip() or r.stderr.strip())


def sync():
    """대시보드 코드 + 스냅샷 + 필요한 모듈을 배포 폴더로 복사."""
    ig = shutil.ignore_patterns("__pycache__", "*.pyc", "publish.py")
    shutil.copytree(ROOT / "dashboard", DEPLOY_DIR / "dashboard", dirs_exist_ok=True, ignore=ig)
    (DEPLOY_DIR / "analysis").mkdir(exist_ok=True)
    (DEPLOY_DIR / "agents").mkdir(exist_ok=True)
    for f in ANALYSIS:
        shutil.copy(ROOT / "analysis" / f, DEPLOY_DIR / "analysis" / f)
    for f in AGENTS:
        shutil.copy(ROOT / "agents" / f, DEPLOY_DIR / "agents" / f)


def git_push(msg: str):
    _run("git", "-C", str(DEPLOY_DIR), "add", "-A")
    if not _run("git", "-C", str(DEPLOY_DIR), "status", "--porcelain").stdout.strip():
        print("변경 없음 — push 생략.")
        return
    c = _run("git", "-C", str(DEPLOY_DIR), "commit", "-m", msg)
    print(c.stdout.strip() or c.stderr.strip())
    p = _run("git", "-C", str(DEPLOY_DIR), "push", "origin", "main")
    print((p.stdout + p.stderr).strip())


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not DEPLOY_DIR.exists():
        print(f"[오류] 배포 폴더가 없습니다: {DEPLOY_DIR}\n"
              "DEPLOY_DIR 환경변수로 지정하거나, 개인 배포 레포를 그 경로에 clone 하세요.")
        return
    msg = "update dashboard + 2026 data snapshot"
    if "-m" in sys.argv:
        i = sys.argv.index("-m")
        if i + 1 < len(sys.argv):
            msg = sys.argv[i + 1]

    print("[1/3] 스냅샷 재생성")
    export_snapshot()
    print("[2/3] 배포 폴더 동기화")
    sync()
    print("[3/3] git push")
    git_push(msg)
    print("\n✅ 발행 완료 → Streamlit Cloud 자동 재배포됩니다.")


if __name__ == "__main__":
    main()
