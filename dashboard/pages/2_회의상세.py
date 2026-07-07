"""회의 상세 — 인덱스·문장별 감성·신호 카드 (report_*.md 의 인터랙티브판)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.graph_objects as go
import streamlit as st
import data

st.title("🔎 회의 상세")

m = data.meetings()
if m.empty:
    st.warning("회의 데이터가 없습니다.")
    st.stop()

dates = list(m["date"])
date = st.selectbox("회의 선택", dates, index=len(dates) - 1)

al = data.alert_detail(date)
lab = data.meetings("label_avg")
cw = m[m["date"] == date]["index_value"]
la = lab[lab["date"] == date]["index_value"]

c1, c2, c3 = st.columns(3)
c1.metric(f"{data.method_label('conf_weighted')} 톤", f"{float(cw.iloc[0]):+.4f}" if len(cw) else "—")
c2.metric(f"{data.method_label('label_avg')} 톤", f"{float(la.iloc[0]):+.4f}" if len(la) else "—")
c3.metric("종합 등급", al.grade if al else "—")

# 신호 카드
if al:
    with st.container(border=True):
        st.markdown(f"**{al.grade}** · 신뢰도 {al.confidence:.3f}")
        if al.reaction_ret is not None:
            st.markdown(f"톤 {al.tone:+.3f} · 시장 반응(발표+1일) {al.reaction_ret:+.2f}%")
        fired = [s for s in al.signals if s.fired]
        if fired:
            for s in fired:
                st.markdown(f"- {s.detail}")
        else:
            st.markdown("- 발동 신호: 없음")
        st.caption(al.note)

# 문장별 감성
st.subheader("문장별 감성 분해")
sents = data.sentences(date)
if sents.empty:
    st.info("이 회의의 문장 감성 데이터가 없습니다.")
else:
    avg = sents[["p_pos", "p_neu", "p_neg"]].mean() * 100
    st.markdown(f"회의 평균 — 긍정 {avg['p_pos']:.1f}% · 중립 {avg['p_neu']:.1f}% · 부정 {avg['p_neg']:.1f}%")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sents["sentence_idx"], y=sents["p_pos"] * 100, name="긍정", marker_color="#2ca02c"))
    fig.add_trace(go.Bar(x=sents["sentence_idx"], y=sents["p_neu"] * 100, name="중립", marker_color="#bbbbbb"))
    fig.add_trace(go.Bar(x=sents["sentence_idx"], y=sents["p_neg"] * 100, name="부정", marker_color="#d62728"))
    fig.update_layout(barmode="stack", height=340, xaxis_title="문장 번호",
                      yaxis_title="확률 %", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")
    with st.expander("문장 원문 보기"):
        st.dataframe(sents.rename(columns={
            "sentence_idx": "#", "sentence": "문장", "p_pos": "긍정",
            "p_neu": "중립", "p_neg": "부정", "entropy": "불확실성"}),
            width="stretch", hide_index=True)

st.info(data.DISCLAIMER)
