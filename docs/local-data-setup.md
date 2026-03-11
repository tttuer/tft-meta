# 로컬 테스트 데이터 세팅 가이드

Docker 스택을 새로 올리거나 볼륨을 초기화한 후 테스트 데이터를 채우는 순서.

## 전제 조건

```bash
cd backend
docker compose up -d
# 모든 서비스 healthy 대기 (약 60~90초)
docker compose ps
```

---

## 1단계 — DB 마이그레이션

```bash
cd backend
uv run alembic upgrade head
```

기대 출력:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
```

---

## 2단계 — 더미 데이터 시드 (빠른 테스트용)

실제 Riot API 없이 바로 UI를 확인하고 싶을 때:

```bash
uv run python seed_data.py
```

기대 출력: `Seeded 3 comps successfully.`

→ 이렐리아 전사 / 럭스 마법사 / 카이사 사수 3개 컴프가 DB에 저장됨

---

## 3단계 — 실제 매치 데이터 수집 (Riot API 필요)

`.env`에 유효한 `RIOT_API_KEY` 설정 필요 (개발 키는 24시간마다 갱신).

```bash
# 테스트용: KR 서버 소환사 10명만 수집 (매치 약 100개)
uv run python -m pipeline.fetch_matches --region kr --limit 10
```

기대 출력:
```
[kr] --limit 적용: 10명으로 제한
[kr] 수집된 고유 매치 ID: N
[kr] 완료 — 저장: N / 스킵: 0 / 에러: 0
```

---

## 4단계 — 컴프 분석 실행

```bash
# 오늘 수집한 데이터 기준, 최소 샘플 1개 + AI 요약은 상위 3개만
uv run python -m pipeline.analyze_comps --date today --min-samples 1 --ai-limit 3
```

기대 출력:
```
[cluster_and_store] 총 참가자: N (min_samples=1)
클러스터링 완료: N 컴프
AI 요약 완료: 3 컴프
```

> **`--ai-limit 3` 권장 이유:**
> OpenRouter 무료 티어는 분당 20 요청(RPM) 제한이 있음.
> 컴프당 4초 딜레이를 넣어도 20개 × 4초 = 80초 = 15 RPM → 안전하지만 느림.
> 테스트 시 `--ai-limit 3`으로 제한하면 3개 × 4초 = 12초에 완료.
> 프로덕션(Airflow)에서는 기본값(20개) 사용.

---

## 5단계 — API 확인

```bash
# 컴프 목록
curl http://localhost:8000/api/v1/comps

# 메타 요약 (ai_summary 포함 여부 확인)
curl http://localhost:8000/api/v1/meta/summary
```

---

## 전체 초기화 후 재시작 시

볼륨까지 삭제하고 처음부터 다시 할 때:

```bash
cd backend
docker compose down -v          # 컨테이너 + 볼륨 삭제
docker compose up -d            # 재실행 (airflow DB 자동 생성 포함)
uv run alembic upgrade head     # 마이그레이션
uv run python seed_data.py      # 더미 데이터 (선택)
```

---

## 요약 체크리스트

- [ ] `docker compose up -d` — 전체 스택 실행
- [ ] `uv run alembic upgrade head` — 테이블 생성
- [ ] `uv run python seed_data.py` — 더미 3개 (빠른 확인용)
- [ ] `uv run python -m pipeline.fetch_matches --region kr --limit 10` — 실제 데이터
- [ ] `uv run python -m pipeline.analyze_comps --date today --min-samples 1` — 컴프 분석
- [ ] `curl http://localhost:8000/api/v1/comps` — 데이터 확인
