"""백테스트 — 신호별 적중률 vs 단순보유(기저율), 95% CI."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st
import data

st.title("🎯 백테스트 — 적중률 vs 단순보유")
st.caption("위험사건 = 발표 후 2거래일 최대낙폭 상위 tertile. 적중률이 기저율(≈34%)보다 "
           "유의하게 높아야 신호가 정보를 가짐. (수치는 백테스트 모듈 재사용 → 리포트와 동일)")

bt = data.backtest()
if bt.empty:
    st.warning("백테스트 데이터가 없습니다.")
    st.stop()

base = float(bt["base_rate"].iloc[0])
fig = go.Figure()
fig.add_trace(go.Bar(
    x=bt["label"], y=bt["hit_rate"], name="적중률",
    marker_color=["#d62728", "#ff7f0e", "#1f77b4"][:len(bt)],
    error_y=dict(type="data", symmetric=False,
                 array=(bt["ci_high"] - bt["hit_rate"]),
                 arrayminus=(bt["hit_rate"] - bt["ci_low"])),
    text=[f"{v:.0%}" for v in bt["hit_rate"]], textposition="outside"))
fig.add_hline(y=base, line_dash="dash", line_color="#333333",
              annotation_text=f"단순보유 기저율 {base:.0%}")
fig.update_layout(height=430, yaxis_title="적중률", yaxis_tickformat=".0%",
                  yaxis_range=[0, 1])
st.plotly_chart(fig, width="stretch")

show = bt.drop(columns=["signal"]).copy()   # 내부 식별자 숨기고 label만 표시
for c in ("hit_rate", "ci_low", "ci_high", "base_rate", "lift"):
    show[c] = (show[c] * 100).round(0).astype(int).astype(str) + "%"
show["판정"] = ["우연 아님(유의)" if p <= 0.05 and l0 > 0 else "근거 약함"
              for p, l0 in zip(bt["rand_p"], bt["lift"])]
st.dataframe(
    show.rename(columns={"label": "신호", "n_fired": "발동", "n_hit": "적중",
                         "hit_rate": "적중률", "ci_low": "적중률 하한", "ci_high": "적중률 상한",
                         "base_rate": "기저율", "lift": "단순보유 대비", "rand_p": "우연일 확률"}),
    width="stretch", hide_index=True)
st.caption("• **적중률 하한·상한** = 실제 적중률이 이 범위에 있을 가능성 95%(표본 적으면 넓어짐)  "
           "• **기저율** = 아무 신호 없이 나오는 비율(단순보유)  "
           "• **단순보유 대비** = 기저율보다 높은 정도(+면 신호가 더 잘 맞음)  "
           "• **우연일 확률** = 무작위 신호가 이만큼 맞출 확률(낮을수록 신호 신뢰↑)")
st.info(data.DISCLAIMER)
