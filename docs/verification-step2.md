# STEP 2 런타임 검증 가이드

STEP 2 (Airflow 파이프라인 확장) 구현 완료 후 순서대로 실행하여 검증합니다.

## 사전 조건

- Docker Desktop 실행 중
- `backend/.env` 파일에 아래 값 설정 완료:
  ```
  RIOT_API_KEY=<발급받은 키>
  OPENROUTER_API_KEY=<발급받은 키>
  SLACK_WEBHOOK_URL=<선택사항>
  ```

---

## 1단계 — 기본 스택 확인

```bash
cd backend
docker compose ps
```

기대: `api`, `db`, `redis` 모두 `healthy` 상태

```bash
curl http://localhost:8000/health
```

기대:
```json
{"status": "ok", "db_connected": true, "version": "0.1.0"}
```

---

## 2단계 — 전체 스택 실행 (Airflow 포함)

`docker-compose.yml`에 모든 서비스가 정의되어 있으므로 한 번에 실행합니다.

```bash
cd backend
docker compose up -d
```

`airflow-init`이 먼저 완료된 후 webserver/scheduler가 자동으로 뜨도록 `depends_on` 조건이 설정되어 있습니다.

전체 서비스 상태 확인 (웹서버 healthy까지 약 60~90초 소요):

```bash
docker compose ps
```

기대: 아래 6개 서비스 모두 정상
```
api               healthy
db                healthy
redis             healthy
airflow-init      Exited (0)   ← 초기화 후 종료됨 (정상)
airflow-webserver healthy
airflow-scheduler running
```

---

## 3단계 — fetch_matches dry-run

실제 DB 저장 없이 매치 수집 로직만 검증합니다.

```bash
cd backend
uv run python -m pipeline.fetch_matches --region kr --dry-run
```

기대 출력:
```
[fetch_matches] KR: N match IDs collected (dry-run, not stored)
```

오류 시 확인:
- `RIOT_API_KEY` 유효 여부 (개발 키는 24시간마다 갱신 필요)
- 네트워크 연결 상태

---

## 4단계 — analyze_comps 실행

```bash
uv run python -m pipeline.analyze_comps --date yesterday
```

기대 출력:
```
[analyze_comps] Stored N comps (max 20)
```

오류 시 확인:
- `match_raw` 테이블에 데이터가 있는지 확인 (3단계를 `--dry-run` 없이 실행 필요)
- DB 연결 상태

> **참고:** `--dry-run` 없이 fetch_matches를 실행하면 실제 데이터가 저장되어 analyze_comps를 정상 테스트할 수 있습니다.
> ```bash
> uv run python -m pipeline.fetch_matches --region kr
> ```

---

## 5단계 — meta summary API

```bash
curl http://localhost:8000/api/v1/meta/summary
```

기대: `ai_summary` 필드가 포함된 JSON 응답

```json
{
  "patch_version": "14.x",
  "top_comps": [...],
  "ai_summary": "현재 메타는 ...",
  "generated_at": "..."
}
```

오류 시 확인:
- `OPENROUTER_API_KEY` 설정 여부
- comps 테이블에 데이터 존재 여부 (4단계 선행 필요)

---

## 6단계 — augments API

```bash
curl "http://localhost:8000/api/v1/augments/best?patch_version=14.x"
```

기대: 스테이지별 (`2-1`, `3-2`, `4-2`) TOP 3 증강 목록

---

## 7단계 — Airflow UI에서 DAG 검증

1. 브라우저에서 `http://localhost:8080` 접속
2. 계정: `admin` / `admin`
3. DAG 목록에서 `tft_daily_meta_update` 확인
4. 토글을 켜서 DAG 활성화
5. 우측 "▶ Trigger DAG" 버튼 클릭 → 수동 실행
6. 7개 태스크 모두 성공(초록) 확인:
   - `fetch_matches`
   - `parse_matches`
   - `cluster_comps`
   - `calculate_stats`
   - `generate_ai_summary`
   - `update_cache`
   - `send_push_notification`

오류 시: 실패 태스크 클릭 → "Log" 탭에서 에러 메시지 확인

---

## 8단계 — Slack 알림 테스트 (선택)

`SLACK_WEBHOOK_URL`이 설정된 경우, DAG 태스크가 실패하면 Slack 채널에 자동 알림이 전송됩니다.

메시지 형식:
```
[TFT Pipeline] fetch_matches 실패 - <에러 메시지> (2026-03-09 04:00:00 KST)
```

---

## 검증 완료 체크리스트

- [ ] 1단계: `api`, `db`, `redis` healthy, `/health` 200 OK
- [ ] 2단계: Airflow 3개 서비스 정상 실행
- [ ] 3단계: `fetch_matches --dry-run` 매치 ID 수 출력
- [ ] 4단계: `analyze_comps` 실행 후 comps 저장 확인
- [ ] 5단계: `GET /api/v1/meta/summary` 응답에 `ai_summary` 포함
- [ ] 6단계: `GET /api/v1/augments/best` 스테이지별 데이터 반환
- [ ] 7단계: Airflow DAG 수동 트리거 7개 태스크 모두 성공
- [ ] 8단계: Slack 알림 수신 (선택)

모든 항목 통과 시 **STEP 3 (Flutter 앱)** 진행.
