"""신호·괴리 — 전 회의 등급표 + 톤↔시장반응 산점도(괴리 시각화)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st
import data

st.title("⚠️ 신호 · 괴리")

al = data.alerts()
if al.empty:
    st.warning("신호 데이터가 없습니다.")
    st.stop()

c1, c2 = st.columns(2)
grades = c1.multiselect("등급 필터", sorted(al["grade"].unique()), default=list(al["grade"].unique()))
regimes = c2.multiselect("국면 필터", sorted(al["regime"].unique()), default=list(al["regime"].unique()))
f = al[al["grade"].isin(grades) & al["regime"].isin(regimes)]

# 산점도: x=톤, y=시장반응, 색=등급 → 2·4분면(부호 반대)이 괴리
sc = f.dropna(subset=["tone", "reaction_ret"])
GRADE_COLOR = {"🟢 정합": "#2ca02c", "⚪ 중립": "#999999",
               "⚠️ 주의": "#ff7f0e", "🔴 경고": "#d62728"}
fig = px.scatter(sc, x="tone", y="reaction_ret", color="grade",
                 color_discrete_map=GRADE_COLOR, hover_data=["date", "regime", "fired"],
                 labels={"tone": "Fed 톤", "reaction_ret": "시장 반응 % (발표+1일)"})
fig.add_hline(y=0, line_dash="dot", line_color="#bbbbbb")
fig.add_vline(x=0, line_dash="dot", line_color="#bbbbbb")
fig.update_layout(height=460, legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig, width="stretch")
st.caption("좌상·우하 사분면(톤과 반응의 부호가 반대) = 괴리. 🔴 경고가 여기에 몰림.")

st.subheader(f"회의 목록 ({len(f)}건)")
st.dataframe(
    f.rename(columns={"date": "회의", "grade": "등급", "confidence": "신뢰도",
                      "tone": "톤", "reaction_ret": "반응%", "fired": "발동신호", "regime": "국면"}),
    width="stretch", hide_index=True)
st.info(data.DISCLAIMER)
