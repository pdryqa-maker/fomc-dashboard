"""운영 — 파이프라인 성공률 · 실행 로그 · '새 회의 처리' 실행 버튼."""
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
import data

st.title("⚙️ 운영 — 파이프라인 성공률")

rn = data.runs()
if rn.empty or "ok" not in rn.columns:
    st.info("아직 실행 기록이 없습니다. 아래 버튼으로 무인 파이프라인을 실행하세요.")
else:
    ok, total = int(rn["ok"].sum()), len(rn)
    partial = int((rn["status"].astype(str).str.startswith("부분오류")).sum()) if "status" in rn else 0
    failed = int((rn["status"].astype(str).str.startswith("실패")).sum()) if "status" in rn else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("성공률", f"{ok/total:.0%}", f"{ok}/{total}건")
    c2.metric("부분오류", f"{partial}건")
    c3.metric("실패", f"{failed}건")
    st.dataframe(rn.tail(20).iloc[::-1], width="stretch", hide_index=True)

st.divider()
st.subheader("새 회의 무인 처리")
st.caption("리포트가 아직 없는 회의를 찾아 멀티에이전트 파이프라인으로 처리합니다 "
           "(FinBERT·네트워크 필요, 몇 분 소요될 수 있음).")

if not data.can_run_pipeline():
    st.info("이 배포(클라우드·모델 없는 읽기전용)에서는 실행 버튼이 비활성화됩니다. "
            "로컬에서 `streamlit run dashboard/app.py` 로 띄우면 사용 가능합니다.")
elif st.button("▶️ 스케줄러 실행 (미처리 회의)", type="primary"):
    with st.spinner("파이프라인 실행 중... (모델 로드 + 처리)"):
        env = {**os.environ, "PYTHONUTF8": "1", "SENTIMENT_ENGINE": "finbert"}
        r = subprocess.run([sys.executable, "agents/scheduler.py"],
                           cwd=str(data.ROOT), capture_output=True, text=True, env=env)
    st.code((r.stdout or "") + ("\n[stderr]\n" + r.stderr if r.stderr else ""))
    data.runs.clear()   # 캐시 무효화 → 최신 성공률 반영
    st.success("완료. 위 성공률·로그가 갱신됩니다.")
    st.rerun()

st.info(data.DISCLAIMER)
