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
st.subheader("🔄 전체 데이터 갱신 (에이전트)")
st.caption("새 FOMC 회의 감성 → 시장(S&P·VIX) → 거시(FRED)를 갱신 에이전트가 한 번에 "
           "처리해 대시보드 DB에 반영합니다. 끝나면 화면이 자동 새로고침됩니다. "
           "(FinBERT·네트워크 필요, 새 회의 수에 따라 몇 분 소요)")

col_a, col_b = st.columns(2)
if not data.can_run_pipeline():
    st.info("이 배포(클라우드·모델 없는 읽기전용)에서는 갱신 버튼이 비활성화됩니다. "
            "로컬에서 `streamlit run dashboard/app.py` 로 띄우면 사용 가능합니다.")
else:
    new_only = not col_b.toggle("전체 재처리(느림)", value=False,
                                help="끄면 새 회의만 처리(빠름). 켜면 모든 회의 재처리.")
    if col_a.button("▶️ 전체 갱신 실행", type="primary"):
        args = ["agents/refresh.py"] + ([] if new_only else ["--all"])
        with st.spinner("갱신 에이전트 실행 중... (감성분석 → 시장 → 거시)"):
            env = {**os.environ, "PYTHONUTF8": "1", "SENTIMENT_ENGINE": "finbert"}
            r = subprocess.run([sys.executable] + args,
                               cwd=str(data.ROOT), capture_output=True, text=True, env=env)
        st.code((r.stdout or "") + ("\n[stderr]\n" + r.stderr if r.stderr else ""))
        st.cache_data.clear()   # 대시보드 전체 캐시 비우기 → 새 데이터 반영
        st.success("갱신 완료. 데이터가 새로고침됩니다.")
        st.rerun()

st.info(data.DISCLAIMER)
