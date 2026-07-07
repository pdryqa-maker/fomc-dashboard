"""거시 정합성 — 회의 톤 vs FRED 경제지표(실업률·근원PCE·국채금리 등)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import data

st.title("🏛️ 거시 정합성 — 톤 vs 경제지표 (FRED)")

if not data.has_macro():
    st.warning("거시 데이터(macro 테이블)가 비어 있습니다. "
               "`python analysis/collect_macro.py` 로 FRED 지표를 먼저 수집하세요.")
    st.stop()

SERIES = {"실업률 (UNRATE)": "UNRATE", "근원PCE 물가 (PCEPILFE)": "PCEPILFE",
          "2년물 채권금리 (DGS2)": "DGS2", "10년물 채권금리 (DGS10)": "DGS10",
          "정책금리 (FEDFUNDS)": "FEDFUNDS"}
label = st.selectbox("비교 지표", list(SERIES.keys()))
sid = SERIES[label]

m = data.meetings()
mc = data.macro(sid)
if m.empty or mc.empty:
    st.warning("데이터가 부족합니다.")
    st.stop()

m = m.copy(); m["date"] = pd.to_datetime(m["date"])
mc = mc.copy(); mc["date"] = pd.to_datetime(mc["date"])

# 회의일 기준 '직전(또는 당일)' 지표값 매칭 → 상관
merged = pd.merge_asof(m.sort_values("date"), mc.sort_values("date"),
                       on="date", direction="backward").dropna(subset=["value"])
corr = merged["index_value"].corr(merged["value"]) if len(merged) > 2 else float("nan")

c1, c2 = st.columns(2)
c1.metric("톤 ↔ 지표 상관(회의 시점)", f"{corr:+.2f}" if corr == corr else "N/A")
c2.metric("표본", f"{len(merged)}건")

fig = go.Figure()
fig.add_trace(go.Scatter(x=m["date"], y=m["index_value"], mode="lines+markers",
                         name="Fed 톤", line=dict(color="#1f77b4")))
fig.add_trace(go.Scatter(x=mc["date"], y=mc["value"], name=label,
                         yaxis="y2", line=dict(color="#9467bd", width=1)))
fig.add_hline(y=0, line_dash="dot", line_color="#bbbbbb")
fig.update_layout(height=480, yaxis_title="Fed 톤",
                  yaxis2=dict(title=label, overlaying="y", side="right"),
                  hovermode="x unified", legend=dict(orientation="h", y=1.06))
st.plotly_chart(fig, width="stretch")

st.caption("우리 FinBERT는 '경제 감성'을 재므로 고용·물가 같은 경제상황 지표와 정합이 자연스럽고, "
           "금리·정책금리는 '정책 반응'이라 국면 의존적(상관이 뒤집힐 수 있음).")
st.info(data.DISCLAIMER)
