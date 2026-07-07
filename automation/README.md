# automation — 대시보드 자동 갱신 도구 (참고·백업)

이 폴더의 스크립트들은 **로컬 전체 프로젝트**(FinBERT 모델·수집 파이프라인이 있는 곳)에서
실행됩니다. **Streamlit Cloud 앱(이 레포의 `dashboard/`)과는 무관**하며, 클라우드에선
실행되지 않습니다(모델·파이프라인 없음). 여기엔 **버전 관리·백업 목적**으로 보관합니다.

## 자동 갱신 흐름
```
매일 (Windows 작업 스케줄러) → run_update.bat → update.py
   ├─ refresh.py : 새 FOMC 회의 감성(FinBERT) + 시장(yfinance) + 거시(FRED) → fomc.db
   └─ publish.py : 스냅샷(CSV) 재생성 → 이 배포 레포에 git push → Streamlit Cloud 자동 재배포
```

| 파일 | 역할 |
|---|---|
| `update.py` | 원커맨드: 갱신(refresh) → 발행(publish) |
| `refresh.py` | 로컬 데이터 갱신 (감성·시장·거시 → fomc.db) |
| `publish.py` | 스냅샷 내보내기 + 배포 레포 push |
| `run_update.bat` | 작업 스케줄러용 래퍼(환경변수·로그) |

## 사용 (로컬 전체 프로젝트에서)
```bash
python update.py            # 새 회의만 갱신 + 발행
python update.py --all      # 전체 재처리 + 발행
python update.py --no-publish   # 로컬만
```

## 스케줄러 관리 (Windows)
- 시간/주기 변경: `taskschd.msc` → "FOMC-Dashboard-Update"
- 끄기/삭제: `Disable-ScheduledTask` / `Unregister-ScheduledTask -TaskName FOMC-Dashboard-Update`
- 로그: 로컬 프로젝트의 `logs/scheduler.log`
