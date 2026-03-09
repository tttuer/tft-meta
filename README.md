# TFT Meta Advisor

TFT(Teamfight Tactics) 메타 분석 컴패니언 앱 — Flutter + FastAPI + K3s

## 로컬 개발 실행 방법

### 사전 준비

- [uv](https://docs.astral.sh/uv/) 설치
- Docker Desktop (또는 Docker Engine + Compose v2)

### 1. 환경변수 설정

```bash
cd backend
cp .env.example .env
# .env 파일에 RIOT_API_KEY 등 입력
```

### 2. 로컬 스택 실행 (API + PostgreSQL + Redis)

```bash
cd backend
docker compose up -d
```

### 3. DB 마이그레이션 (최초 1회)

```bash
cd backend
uv run alembic upgrade head
```

### 4. 더미 데이터 시드

```bash
cd backend
uv run python seed_data.py
```

### 5. 헬스체크 확인

```bash
curl http://localhost:8000/health
# {"status":"ok","db_connected":true,"version":"0.1.0"}
```

### 6. 컴프 목록 확인

```bash
curl http://localhost:8000/api/v1/comps
```

### 7. Riot API 테스트

```bash
cd backend
uv run python test_riot_api.py
```

## API 문서

로컬 실행 후 http://localhost:8000/docs (Swagger UI)

## 구조

```
backend/         FastAPI 백엔드, Alembic 마이그레이션
pipeline/        Airflow DAG (STEP 2에서 확장)
k8s/             K3s 배포 매니페스트 (STEP 5)
contracts/       에이전트 간 공유 계약 (api-spec.yaml)
```

## K3s 배포용 이미지 빌드 (STEP 5)

`docker compose up -d`는 내부적으로 이미지를 자동 빌드하므로 로컬 개발 시 별도 빌드가 불필요합니다.
K3s 배포를 위해 이미지를 직접 빌드할 때만 사용하세요.

```bash
docker build -t tft-meta-api ./backend
```
