"""타임라인 — 회의 톤 시계열 + 시장/거시 오버레이 (보조축)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import data

st.title("📈 타임라인 — 톤 vs 시장·거시")

method = st.selectbox("톤 집계 방식", ["conf_weighted", "label_avg"], index=0,
                      format_func=data.method_label)
m = data.meetings(method)
if m.empty:
    st.warning("회의 데이터가 없습니다.")
    st.stop()
m["date"] = pd.to_datetime(m["date"])

al = data.alerts()
grade_of = dict(zip(al["date"], al["grade"])) if not al.empty else {}
GRADE_COLOR = {"🟢 정합": "#2ca02c", "⚪ 중립": "#999999",
               "⚠️ 주의": "#ff7f0e", "🔴 경고": "#d62728"}
colors = [GRADE_COLOR.get(grade_of.get(d.strftime("%Y-%m-%d"), ""), "#1f77b4") for d in m["date"]]

# 오버레이 선택 (보조축 — 한 번에 하나로 스케일 유지)
overlay = st.selectbox("오버레이 (보조축)",
                       ["없음", "S&P500 지수", "VIX 지수", "2년물 채권금리(DGS2)",
                        "실업률(UNRATE)", "근원PCE 물가(PCEPILFE)"])

fig = go.Figure()
fig.add_trace(go.Scatter(x=m["date"], y=m["index_value"], mode="lines+markers",
                         name="Fed 톤", line=dict(color="#1f77b4"),
                         marker=dict(color=colors, size=8),
                         hovertext=[grade_of.get(d.strftime("%Y-%m-%d"), "") for d in m["date"]]))
fig.add_hline(y=0, line_dash="dot", line_color="#bbbbbb")

if overlay != "없음":
    if overlay in ("S&P500 지수", "VIX 지수"):
        mk = data.market()
        mk["date"] = pd.to_datetime(mk["date"])
        col = "spx_close" if overlay == "S&P500 지수" else "vix"
        sub = mk[["date", col]].dropna()
        fig.add_trace(go.Scatter(x=sub["date"], y=sub[col], name=overlay,
                                 yaxis="y2", line=dict(color="#888888", width=1)))
    else:
        sid = overlay.split("(")[1].rstrip(")")
        mc = data.macro(sid)
        mc["date"] = pd.to_datetime(mc["date"])
        fig.add_trace(go.Scatter(x=mc["date"], y=mc["value"], name=overlay,
                                 yaxis="y2", line=dict(color="#9467bd", width=1)))
    fig.update_layout(yaxis2=dict(title=overlay, overlaying="y", side="right"))

fig.update_layout(height=520, yaxis_title="Fed 톤 지수", hovermode="x unified",
                  legend=dict(orientation="h", y=1.05))
st.plotly_chart(fig, width="stretch")

st.caption("마커 색 = 종합 등급(🟢정합·⚪중립·⚠️주의·🔴경고). 보조축은 스케일 유지를 위해 한 번에 하나만.")
st.info(data.DISCLAIMER)
