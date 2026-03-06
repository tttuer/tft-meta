# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

당신은 TFT Meta Advisor 프로젝트의 테크 리드입니다.
다음 세 서브 에이전트를 조율하여 프로젝트를 완성하세요.

## 에이전트 구성
- backend-agent:   백엔드 API, 데이터 파이프라인 담당 (STEP 1, 2)
- frontend-agent:  Flutter 앱 담당 (STEP 3, 4)
- devops-agent:    K3s 배포 담당 (STEP 5)

## 작업 순서 규칙
1. backend-agent가 contracts/api-spec.yaml 을 먼저 작성하면
2. frontend-agent와 devops-agent가 동시에 작업을 시작할 수 있습니다.
3. 각 에이전트는 작업 완료 시 contracts/에 결과물을 기록합니다.

## 현재 명령
backend-agent를 먼저 실행하여 STEP 1을 시작하세요.
완료 후 frontend-agent와 devops-agent에게 각각의 STEP을 지시하세요.

## Project Overview

TFT Meta Advisor is a multi-component platform for Teamfight Tactics meta analysis, consisting of:
- A **Flutter mobile app** with custom board rendering and platform-specific overlays
- A **FastAPI backend** integrating with the Riot Games API
- An **Apache Airflow** data pipeline for AI-driven meta analysis
- **K3s/Kubernetes** deployment infrastructure

## Repository Structure

```
contracts/          # Shared contracts between agents (source of truth)
  api-spec.yaml     # OpenAPI 3.0 spec — ALL backend endpoints, env vars, image names
  flutter-build.md  # Flutter build artifact locations and commands

backend/            # FastAPI app, PostgreSQL (Alembic migrations), Redis, Riot API client
pipeline/           # Apache Airflow DAGs for data ingestion and AI analysis
flutter_app/        # Flutter mobile app (lib/core/api_client.dart, lib/core/env_config.dart)
k8s/                # Kubernetes manifests (namespace: tft-meta)
scripts/            # Deployment scripts (scripts/deploy.sh)
```

## Agent System

This project uses specialized sub-agents defined in `.claude/agents/`:

| Agent | Scope | Trigger |
|-------|-------|---------|
| `backend-agent` | `backend/`, `pipeline/`, `contracts/api-spec.yaml` | FastAPI endpoints, DB schema, Riot API, Airflow DAGs |
| `frontend-agent` | `flutter_app/` | Flutter screens, CustomPainter, Android overlay, iOS widgets |
| `devops-agent` | `k8s/`, `scripts/` | K3s manifests, deploy.sh, Ingress configuration |

**Directory access is strictly enforced** — each agent must not touch directories outside its scope.

## Contracts as Source of Truth

`contracts/api-spec.yaml` is the integration contract between all agents:
- Backend updates it after every meaningful change
- Frontend reads it before implementing any API call
- DevOps reads it to get image names, ports, and env vars before any deployment

`contracts/flutter-build.md` is read by devops-agent before any deployment to locate build artifacts.

## Key Architecture Decisions

### Backend
- FastAPI with Pydantic v2, async/await throughout
- PostgreSQL with Alembic migrations (never alter tables manually)
- Redis caching: static data TTL 1hr, match data TTL 24hr
- Riot API rate limits: 20 req/1s, 100 req/2min — use exponential backoff with jitter
- UUID primary keys for player/match entities; `created_at`/`updated_at` on all records
- Router structure: `/champions`, `/matches`, `/meta`, `/players`, `/health`

### Flutter App
- All API calls MUST go through `lib/core/api_client.dart` — no direct HTTP calls
- All API base URLs and endpoints sourced from `lib/core/env_config.dart` — no hardcoded URLs
- Model classes must match schemas defined in `contracts/api-spec.yaml`
- Android overlay: `SYSTEM_ALERT_WINDOW` permission + MethodChannel for Flutter/native comms
- iOS: WidgetKit + ActivityKit, App Groups for data sharing

### K3s Deployment
- All resources in `namespace: tft-meta`
- Required labels on all resources: `app: tft-meta`, `managed-by: devops-agent`
- All secrets via `kubectl create secret` — never hardcoded in manifests
- `scripts/deploy.sh` must be idempotent and deploy the full stack in one command
- Deployment order: namespace → configmaps → deployments → services → ingress

## Build Commands

### Flutter
Build commands are recorded in `contracts/flutter-build.md` after each frontend task. Check that file for the current commands.

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Airflow Pipeline
```bash
cd pipeline
airflow db init
airflow scheduler &
airflow webserver --port 8080
```

### K3s Deployment
```bash
# Create required secrets first (see k8s/README or devops-agent output)
kubectl create secret generic tft-meta-secret --namespace=tft-meta \
  --from-literal=DATABASE_URL='...' \
  --from-literal=RIOT_API_KEY='...' \
  --from-literal=REDIS_URL='...'

# Deploy full stack
bash scripts/deploy.sh
```

## Environment Variables

Defined in `contracts/api-spec.yaml` under `x-environment-variables`. Key vars:
- `DATABASE_URL` — PostgreSQL connection string
- `RIOT_API_KEY` — Riot Games API key
- `REDIS_URL` — Redis connection string