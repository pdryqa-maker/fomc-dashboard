# FOMC 감성분석 대시보드 (Streamlit)

FOMC 성명문 감성(FinBERT) → 지수 → 시장·거시(FRED) 비교 → 신호 → 백테스트를
브라우저에서 탐색하는 **읽기전용** 대시보드. (2026-AICP 팀 연구의 대시보드 부분)

> 이 레포는 **배포 전용 경량 사본**입니다. 대시보드 실행에 필요한 코드와
> **데이터 스냅샷**(`dashboard/snapshot/*.csv`)만 담았습니다. 모델·원천 파이프라인·
> 비밀키는 포함하지 않습니다(수치·문장 스냅샷만, 읽기전용).

## 실행 (로컬)
```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## 배포 (Streamlit Community Cloud)
share.streamlit.io → New app → 이 레포 · Branch `main` · Main file `dashboard/app.py`.
데이터는 스냅샷 CSV로 동작하므로 별도 DB·모델 불필요.

## 페이지
개요 · 타임라인 · 회의상세 · 신호/괴리 · 백테스트 · 거시정합성 · 운영.

## 면책
연구·참고용이며 투자 조언이 아닙니다. 상관≠인과 · 표본 제한.
