"""대시보드 공용 데이터 로더 (읽기 전용, 캐시).

원칙: 숫자를 새로 계산하지 않고 검증된 함수(analysis.signals·backtest·agents.runlog)를
그대로 재사용 → 리포트와 값이 100% 일치. DB는 data/fomc.db(188회의·시장·거시).
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.signals import signal_label, method_label  # 사용자용 라벨 (재노출)

DB = ROOT / "data" / "fomc.db"
SNAPSHOT = Path(__file__).resolve().parent / "snapshot"


@st.cache_resource(show_spinner=False)
def _snapshot_db_path() -> str:
    """커밋된 스냅샷 CSV로 임시 sqlite 재구성 (클라우드 폴백). 1회만 빌드(캐시)."""
    path = Path(tempfile.gettempdir()) / "fomc_snapshot.db"
    con = sqlite3.connect(path)
    for name in ("meetings", "market", "macro", "sentences", "news", "news_articles"):
        f = SNAPSHOT / f"{name}.csv"
        if f.exists():
            pd.read_csv(f).to_sql(name, con, if_exists="replace", index=False)
    con.commit()
    con.close()
    return str(path)


def _con():
    """로컬은 fomc.db, 없으면(클라우드) 스냅샷으로 재구성한 임시 DB."""
    if DB.exists():
        return sqlite3.connect(DB)
    return sqlite3.connect(_snapshot_db_path())


def can_run_pipeline() -> bool:
    """실행 버튼 가능 여부 — FinBERT 모델이 로컬에 있을 때만(클라우드에선 False)."""
    return (ROOT / "models" / "finbert-finetuned").exists() and DB.exists()


@st.cache_data(show_spinner=False)
def meetings(method: str = "conf_weighted") -> pd.DataFrame:
    con = _con()
    df = pd.read_sql_query(
        "SELECT date, index_value, confidence FROM meetings "
        "WHERE method=? AND granularity='meeting' ORDER BY date",
        con, params=(method,))
    con.close()
    return df


@st.cache_data(show_spinner=False)
def market() -> pd.DataFrame:
    con = _con()
    df = pd.read_sql_query("SELECT * FROM market ORDER BY date", con)
    con.close()
    return df


@st.cache_data(show_spinner=False)
def macro(series: str) -> pd.DataFrame:
    con = _con()
    df = pd.read_sql_query(
        "SELECT date, value FROM macro WHERE series=? ORDER BY date",
        con, params=(series,))
    con.close()
    return df


@st.cache_data(show_spinner=False)
def has_macro() -> bool:
    con = _con()
    try:
        n = con.execute("SELECT COUNT(*) FROM macro").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    con.close()
    return n > 0


@st.cache_data(show_spinner=False)
def has_news() -> bool:
    con = _con()
    try:
        n = con.execute("SELECT COUNT(1) FROM news").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    con.close()
    return n > 0


@st.cache_data(show_spinner=False)
def news() -> pd.DataFrame:
    """일별 News 감성 지수(+CI)."""
    con = _con()
    try:
        df = pd.read_sql_query(
            "SELECT date, n_articles, conf_weighted, ci_lo, ci_hi, confidence "
            "FROM news ORDER BY date", con)
    except Exception:
        df = pd.DataFrame()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def news_articles(limit: int = 30) -> pd.DataFrame:
    """최신 뉴스 기사(감성 포함)."""
    con = _con()
    try:
        df = pd.read_sql_query(
            "SELECT date, title, source, score, p_pos, p_neg FROM news_articles "
            "ORDER BY date DESC, score DESC LIMIT ?", con, params=(limit,))
    except Exception:
        df = pd.DataFrame()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def sentences(date: str) -> pd.DataFrame:
    con = _con()
    df = pd.read_sql_query(
        "SELECT sentence_idx, sentence, p_pos, p_neu, p_neg, entropy "
        "FROM sentences WHERE date=? ORDER BY sentence_idx", con, params=(date,))
    con.close()
    return df


@st.cache_data(show_spinner=False)
def alerts() -> pd.DataFrame:
    """회의별 종합 알림 (signals.build_alerts 재사용) → DataFrame."""
    from analysis.signals import load_series, build_alerts
    from analysis.backtest import regime_of
    con = _con()
    series = load_series(con)
    con.close()
    al = build_alerts(series, small_sample=len(series) < 30)
    return pd.DataFrame([{
        "date": a.date, "grade": a.grade, "confidence": a.confidence,
        "tone": a.tone, "reaction_ret": a.reaction_ret,
        "fired": ", ".join(a.fired_labels()) or "-",
        "regime": regime_of(a.date),
    } for a in al])


@st.cache_data(show_spinner=False)
def alert_detail(date: str):
    """특정 회의의 Alert 객체(신호 카드용)."""
    from analysis.signals import load_series, build_alerts
    con = _con()
    series = load_series(con)
    con.close()
    al = build_alerts(series, small_sample=len(series) < 30)
    return next((a for a in al if a.date == date), None)


@st.cache_data(show_spinner=False)
def backtest() -> pd.DataFrame:
    """신호별 적중률 vs 기저율 (backtest 순수함수 재사용) → 리포트와 동일 수치."""
    from analysis.signals import load_series, build_alerts, Thresholds, signal_label
    from analysis.backtest import load_outcomes, risk_flags, evaluate, N_DAYS
    con = _con()
    series = load_series(con)
    dates = [s["date"] for s in series]
    al = build_alerts(series, Thresholds(), small_sample=len(series) < 30)
    dds, _ = load_outcomes(con, dates, N_DAYS)
    con.close()
    valid = [i for i in range(len(dates)) if dds[i] is not None]
    v_dd = [dds[i] for i in valid]
    risk = risk_flags(v_dd)
    risk_map = {valid[j]: risk[j] for j in range(len(valid))}
    out = []
    for name in ("divergence", "tone_vs_vix", "tone_shift"):
        fired = [any(s.name == name and s.fired for s in al[i].signals) for i in valid]
        rk = [risk_map[i] for i in valid]
        res = evaluate(fired, rk)
        out.append({"signal": name, "label": signal_label(name),
                    "n_fired": res.n_fired, "n_hit": res.n_hit,
                    "hit_rate": res.hit_rate, "ci_low": res.ci_low, "ci_high": res.ci_high,
                    "base_rate": res.base_rate, "lift": res.lift, "rand_p": res.rand_p})
    return pd.DataFrame(out)


@st.cache_data(show_spinner=False)
def runs() -> pd.DataFrame:
    """파이프라인 실행 로그(runlog) → DataFrame. 없으면 스냅샷 폴백."""
    from agents.runlog import read_runs
    r = read_runs()
    if r:
        return pd.DataFrame(r)
    snap = SNAPSHOT / "runs.csv"
    if snap.exists():
        return pd.read_csv(snap)
    return pd.DataFrame()


DISCLAIMER = ("⚠️ 연구·참고용 정보이며 투자 조언이 아닙니다. "
              "상관≠인과 · 표본 제한 · 톤≠정책스탠스. 과거 경향이 미래를 보장하지 않습니다.")
