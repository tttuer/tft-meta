# TFT Meta Advisor

TFT(Teamfight Tactics) 메타 분석 컴패니언 앱 — Flutter + FastAPI + Airflow + K3s

## 프로젝트 구조

```
backend/           FastAPI 백엔드 (API 서버, PostgreSQL, Redis, Riot API 클라이언트)
backend/pipeline/  Airflow DAG + 수집·분석 스크립트
flutter_app/       Flutter 모바일 앱
contracts/         에이전트 간 공유 계약 (api-spec.yaml, flutter-build.md)
k8s/               K3s 배포 매니페스트 (STEP 5)
scripts/           배포 스크립트 (STEP 5)
```

---

## 로컬 개발 — 빠른 시작

### 사전 준비

- [uv](https://docs.astral.sh/uv/) 설치
- Docker Desktop (또는 Docker Engine + Compose v2)
- Flutter SDK
- Riot API 키 — [developer.riotgames.com](https://developer.riotgames.com) (24시간마다 갱신)

### 1. 환경변수 설정

```bash
cd backend
cp .env.example .env
# .env 파일 편집 (아래 항목 입력)
```

`.env` 필수 항목:

```dotenv
RIOT_API_KEY=RGAPI-xxxx-xxxx-xxxx

# AI 요약용 (둘 중 하나 — 발급 방법은 하단 참조)
GITHUB_TOKEN=gho_xxx          # GitHub Copilot 구독자 (우선 사용)
OPENROUTER_API_KEY=sk-or-xxx  # OpenRouter (무료 모델 있음, 폴백)
```

### 2. 백엔드 스택 실행 (API + PostgreSQL + Redis)

```bash
cd backend
docker compose up -d db redis api
```

### 3. DB 마이그레이션 (최초 1회)

```bash
cd backend
uv run alembic upgrade head
```

### 4. 헬스체크 확인

```bash
curl http://localhost:8000/health
# {"status":"ok","db_connected":true}
```

---

## 데이터 투입 방법

앱을 띄우려면 컴프 데이터가 필요합니다. **더미 데이터** 또는 **실 데이터** 중 선택하세요.

### A) 더미 데이터 (빠름 — Riot API 키 불필요)

```bash
cd backend
uv run python seed_data.py
```

이렐리아 전사(S), 럭스 마법사(A), 카이사 사수(A) 3개 컴프가 삽입됩니다.

---

### B) 실 데이터 — Riot API 수집 파이프라인

로컬에서 실행한 스크립트는 Docker PostgreSQL(`localhost:5432`)에 직접 저장되고,
Flutter 앱은 Docker API(`localhost:8000`)를 통해 같은 DB를 조회합니다.

```
로컬 스크립트 → localhost:5432 (Docker PostgreSQL)
                         ↑
Flutter 앱 → localhost:8000 (Docker API) → 같은 DB 조회
```

#### Step 1. 매치 수집

```bash
cd backend

# 테스트: KR 리전, 소환사 20명만 (~200 매치, 2~3분)
uv run python -m pipeline.fetch_matches --region kr --limit 20

# 저장 없이 카운트만 확인 (dry-run)
uv run python -m pipeline.fetch_matches --region kr --limit 20 --dry-run

# 실전: KR 전체 마스터+
uv run python -m pipeline.fetch_matches --region kr

# 실전: 전 리전 (kr + na1 + euw1)
uv run python -m pipeline.fetch_matches --region all
```

**`--limit N`**: 마스터+ **소환사 수** 제한 (소환사 1명당 최근 10경기 수집).
의미 있는 컴프를 만들려면 `--limit 20` 이상 권장.

#### Step 2. 컴프 클러스터링 + AI 요약 생성

```bash
cd backend

# 테스트: 샘플 수 기준 낮추고 AI 요약 3개만
uv run python -m pipeline.analyze_comps --date today --min-samples 5 --ai-limit 3

# 실전: 기본값
uv run python -m pipeline.analyze_comps --date today
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--date` | yesterday | 분석 날짜 (`today` / `yesterday` / `YYYY-MM-DD`) |
| `--min-samples` | 50 | 컴프로 인정할 최소 참가자 수. 테스트 시 **5~10** 권장 |
| `--ai-limit` | 20 | AI 요약 생성 컴프 수. 테스트 시 **3 이하** 권장 |

#### 전체 실행 순서 요약

```bash
# 터미널 1: 백엔드 유지
cd backend && docker compose up -d db redis api

# 터미널 2: 수집 → 분석 순서대로
cd backend
uv run python -m pipeline.fetch_matches --region kr --limit 20
uv run python -m pipeline.analyze_comps --date today --min-samples 5 --ai-limit 3
```

---

## Flutter 앱 실행

```bash
cd flutter_app
flutter pub get
```

| 환경 | 명령 | API 연결 주소 |
|------|------|--------------|
| Android 에뮬레이터 | `flutter run --dart-define=ENV=android` | `http://10.0.2.2:8000` |
| 웹 브라우저 (Chrome) | `flutter run -d chrome --dart-define=ENV=development` | `http://localhost:8000` |
| 실기기 (Android) | `flutter run --dart-define=ENV=android` + `env_config.dart`에서 IP 수정 | `http://192.168.x.x:8000` |

> **Android 에뮬레이터는 `localhost`가 에뮬레이터 자신**을 가리키므로 `10.0.2.2`를 사용합니다.
> 이미 `ENV=android` 케이스로 처리되어 있어 별도 수정 불필요.

### 테스트 / 정적 분석

```bash
cd flutter_app
flutter test      # 24개 위젯 테스트
flutter analyze   # 정적 분석 (No issues 목표)
```

---

## API 문서

로컬 실행 후 http://localhost:8000/docs (Swagger UI)

---

## Airflow 웹 UI (선택)

```bash
cd backend
docker compose up -d airflow-init airflow-webserver airflow-scheduler
# http://localhost:8080  (admin / admin)
```

DAG `tft_daily_meta_update`가 매일 04:00 KST 자동 실행됩니다.

---

## K3s 배포 (STEP 5 — 미구현)

```bash
# 이미지 빌드
docker build -t tft-meta-api ./backend

# 배포 (k8s/, scripts/ 구현 후)
bash scripts/deploy.sh
```

---

## 환경변수 전체 목록

`contracts/api-spec.yaml`의 `x-environment-variables` 섹션 참조.

| 변수 | 필수 | 설명 |
|------|------|------|
| `RIOT_API_KEY` | 실 데이터 수집 시 필수 | Riot Games API 키 (24시간마다 갱신) |
| `DATABASE_URL` | 선택 (Docker 기본값 있음) | PostgreSQL 연결 문자열 |
| `REDIS_URL` | 선택 (Docker 기본값 있음) | Redis 연결 문자열 |
| `GITHUB_TOKEN` | AI 요약 시 선택 | GitHub Copilot 토큰 (발급 방법 하단 참조) |
| `OPENROUTER_API_KEY` | AI 요약 시 선택 | OpenRouter API 키 |
| `SLACK_WEBHOOK_URL` | 선택 | 파이프라인 완료 알림 |

---

## AI 요약 API 키 발급 방법

AI 요약 기능은 **GitHub Copilot(우선)** 또는 **OpenRouter(폴백)** 중 하나가 필요합니다.

### 옵션 A — GitHub Copilot 토큰

> 전제조건: GitHub Copilot **유료 구독** 계정

`gh auth login`으로 받은 토큰은 동작하지 않습니다.
VS Code Copilot 확장의 Client ID로 발급된 토큰이어야 합니다. 전용 스크립트를 사용하세요.

```bash
cd backend
uv run python get_copilot_token.py
```

```
1. 브라우저에서 열기: https://github.com/login/device
2. 코드 입력: XXXX-XXXX

✅ 토큰 발급 성공!
GITHUB_TOKEN=gho_xxxx   ← 이 값을 .env에 저장
```

```dotenv
GITHUB_TOKEN=gho_xxxx
```

> Copilot 구독이 없으면 토큰 발급 후에도 `404 Not Found`가 납니다 — 이 경우 옵션 B를 사용하세요.

---

### 옵션 B — OpenRouter (무료 모델 있음)

1. [openrouter.ai](https://openrouter.ai) 가입 후 API 키 생성
2. `.env`에 입력:

```dotenv
OPENROUTER_API_KEY=sk-or-xxxx
# GITHUB_TOKEN은 비워두거나 삭제 (설정되어 있으면 Copilot이 먼저 시도됨)
```

기본 모델: `meta-llama/llama-3.3-70b-instruct:free` (무료, 분당 20 req 제한)
