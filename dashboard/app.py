"""FOMC 감성 멀티에이전트 — 웹 대시보드 (개요).

실행:  streamlit run dashboard/app.py
읽기 전용: DB·리포트를 시각화. 수치는 검증된 함수 재사용 → 리포트와 일치.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import data

st.set_page_config(page_title="FOMC 감성 대시보드", page_icon="📊", layout="wide")

st.title("📊 FOMC 감성분석 멀티에이전트 — 대시보드")
st.caption("FOMC 성명문(Fed) + 뉴스(News) 감성 → 지수 → 시장·거시 비교 → 신호 → 리포트")
st.info(data.DISCLAIMER)

m = data.meetings()
al = data.alerts()
bt = data.backtest()
rn = data.runs()

# ── KPI ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("분석 회의 수", f"{len(m)}건")

if not al.empty:
    last = al.iloc[-1]
    c2.metric(f"최신 회의 ({last['date']})", last["grade"])
else:
    c2.metric("최신 회의", "—")

if not bt.empty and (bt["signal"] == "divergence").any():
    dv = bt[bt["signal"] == "divergence"].iloc[0]
    c3.metric("반대 방향 신호 적중률", f"{dv['hit_rate']:.0%}",
              f"기저 {dv['base_rate']:.0%} 대비 {dv['lift']:+.0%}")
else:
    c3.metric("반대 방향 신호 적중률", "—")

if not rn.empty and "ok" in rn.columns:
    ok = int(rn["ok"].sum())
    total = len(rn)
    c4.metric("파이프라인 성공률", f"{ok/total:.0%}", f"{ok}/{total}건")
else:
    c4.metric("파이프라인 성공률", "기록 없음")

st.divider()

# ── 최신 회의 카드 ──
st.subheader("최신 회의 요약")
if not al.empty:
    last = al.iloc[-1]
    a, b = st.columns([1, 2])
    a.markdown(f"### {last['grade']}")
    a.caption(f"{last['date']} · 신뢰도 {last['confidence']:.3f} · 국면: {last['regime']}")
    tone = last["tone"]
    reac = last["reaction_ret"]
    reac_str = f"{reac:+.2f}%" if reac is not None else "(데이터 없음)"
    b.markdown(
        f"- **톤**: {tone:+.3f}\n"
        f"- **시장 반응(발표+1일)**: {reac_str}\n"
        f"- **발동 신호**: {last['fired']}")
else:
    st.write("데이터가 없습니다. `SENTIMENT_ENGINE=finbert python pipeline.py` 로 회의를 처리하세요.")

st.divider()
st.caption("← 왼쪽 사이드바에서 타임라인 · 회의상세 · 신호/괴리 · 백테스트 · 거시정합성 · 운영 페이지로 이동")
