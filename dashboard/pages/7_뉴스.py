"""News — Marketaux 실시간 뉴스 감성 지수(+95% CI) + 최신 기사."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import data

st.title("📰 News — 실시간 뉴스 감성")

if not data.has_news():
    st.warning("뉴스 데이터가 없습니다. `python analysis/collect_news.py` 로 수집하거나 "
               "⚙️ 운영 페이지의 '전체 갱신'을 실행하세요.")
    st.stop()

nd = data.news()
if nd.empty:
    st.info("News 지수 데이터가 비어 있습니다.")
    st.stop()
nd = nd.copy()
nd["date"] = pd.to_datetime(nd["date"])

last = nd.iloc[-1]
c1, c2, c3 = st.columns(3)
c1.metric(f"최신 News 지수 ({last['date'].date()})", f"{last['conf_weighted']:+.3f}")
c2.metric("그날 기사 수", int(last["n_articles"]))
c3.metric("수집 일수", len(nd))

# 일별 News 지수 + 95% CI 밴드
fig = go.Figure()
fig.add_trace(go.Scatter(x=nd["date"], y=nd["ci_hi"], line=dict(width=0),
                         showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=nd["date"], y=nd["ci_lo"], fill="tonexty",
                         fillcolor="rgba(31,119,180,0.15)", line=dict(width=0),
                         name="95% CI", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=nd["date"], y=nd["conf_weighted"], mode="lines+markers",
                         name="News 지수", line=dict(color="#1f77b4")))
fig.add_hline(y=0, line_dash="dot", line_color="#bbbbbb")
fig.update_layout(height=420, yaxis_title="News 감성 지수", hovermode="x unified",
                  legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, width="stretch")
st.caption("Marketaux 실시간 Fed·경제 뉴스를 우리 FinBERT로 채점한 **일별 지수**. "
           "95% CI는 그날 기사 수 기반(기사 많을수록 좁아짐). 무료 티어라 **최근 며칠**만 표시.")

st.subheader("최신 기사")
arts = data.news_articles(30)
if arts.empty:
    st.info("기사가 없습니다.")
else:
    a = arts.copy()
    a["감성"] = a["score"].apply(
        lambda s: "🟢 긍정" if s > 0.05 else ("🔴 부정" if s < -0.05 else "⚪ 중립"))
    a["점수"] = a["score"].round(3)
    st.dataframe(
        a.rename(columns={"date": "날짜", "title": "제목", "source": "출처"})[
            ["날짜", "제목", "출처", "감성", "점수"]],
        width="stretch", hide_index=True)

st.info(data.DISCLAIMER)
