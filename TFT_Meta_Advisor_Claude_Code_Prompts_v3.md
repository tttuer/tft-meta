# TFT Meta Advisor — Claude Code 단계별 프롬프트

> **사용 방법**: 각 STEP을 순서대로 Claude Code에 붙여넣어 실행하세요.  
> 다음 단계로 넘어가기 전에 현재 단계의 **완료 조건 체크리스트**를 먼저 확인하세요.

---

## 단계별 진행 요약

| STEP | 핵심 산출물 | 예상 소요 |
|------|------------|----------|
| STEP 1 | FastAPI 백엔드 + PostgreSQL 스키마 + Riot API 연동 | 1주 |
| STEP 2 | Airflow 파이프라인 + 컴프 클러스터링 + AI 요약 엔진 | 1주 |
| STEP 3 | Flutter 앱 4개 화면 + 배치 보드 CustomPainter | 1~2주 |
| STEP 4 | Android 플로팅 버블 오버레이 + iOS 위젯/Live Activities | 1~2주 |
| STEP 5 | K3s 배포 + 오프라인 지원 + 푸시 알림 + 외부 접근 설정 | 1주 |

> **배포 환경**: 단일 노드 K3s (개인 PC) + 외부 접근 (공인 IP/도메인)  
> 백엔드 API, PostgreSQL, Redis, Airflow 파이프라인 모두 K3s에서 운영

---

## STEP 1 — 프로젝트 초기 설정 & 백엔드 기반 구축

```
당신은 TFT(Teamfight Tactics) 메타 분석 컴패니언 앱 "TFT Meta Advisor"의
백엔드를 구축하는 시니어 풀스택 개발자입니다.

## 프로젝트 개요
- TFT 플레이어가 게임 중 실시간으로 최신 메타(고승률 덱 구성)를 확인하는 앱
- 매일 자동으로 Riot API에서 마스터+ 매치 데이터를 수집·분석하여 추천 컴프 제공
- Flutter (Dart) 단일 코드베이스로 Android / iOS / Web 지원
- 배포 환경: 단일 노드 K3s (개인 PC), 외부에서도 접근 가능

## STEP 1 작업 목표
백엔드 API 서버, 데이터베이스 스키마, Riot API 연동을 완성한다.
K3s 배포를 염두에 두고 처음부터 컨테이너 친화적으로 설계한다.

---

## 1. 디렉터리 구조 생성

tft-meta-advisor/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── comp.py
│   │   │   ├── champion.py
│   │   │   ├── item.py
│   │   │   └── augment.py
│   │   ├── routers/
│   │   │   ├── comps.py
│   │   │   ├── champions.py
│   │   │   ├── augments.py
│   │   │   └── meta.py
│   │   ├── services/
│   │   │   ├── riot_api.py
│   │   │   ├── comp_analyzer.py
│   │   │   ├── image_sync.py          # 이미지 URL 수집 및 DB 저장
│   │   │   └── cache.py
│   │   └── schemas/
│   │       └── responses.py
│   ├── pipeline/
│   │   ├── airflow_dag.py
│   │   ├── fetch_matches.py
│   │   └── analyze_comps.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── docker-compose.yml        # 로컬 개발용
├── k8s/                          # K3s 배포 매니페스트 (STEP 5에서 채움)
│   ├── namespace.yaml
│   ├── api/
│   ├── postgres/
│   ├── redis/
│   ├── airflow/
│   └── ingress/
└── README.md

---

## 2. 데이터베이스 스키마 (PostgreSQL + SQLAlchemy 2.0 ORM)

다음 5개 테이블을 생성하라.

### comps 테이블
- id (UUID, PK)
- name (String) — 컴프 이름 예: "이렐리아 전사"
- tier (Enum: S/A/B/C)
- win_rate (Float) — 1위 비율 0.0~1.0
- top4_rate (Float) — 4위 이내 비율
- avg_placement (Float) — 평균 순위
- play_rate (Float) — 픽률
- sample_count (Integer) — 샘플 매치 수
- core_units (JSONB) — 레벨별 코어 챔피언 목록 {"6": [...], "7": [...], "8": [...], "9": [...]}
- board_positions (JSONB) — 배치 좌표 [{"row": 0, "col": 2, "champion_id": "Irelia", "items": [...]}]
- recommended_augments (JSONB) — 스테이지별 추천 증강 {"2-1": [...], "3-2": [...], "4-2": [...]}
- entry_conditions (JSONB) — 진입 조건 텍스트 배열
- ai_summary (Text) — AI 생성 전략 요약
- patch_version (String)
- updated_at (Timestamp)

### champions 테이블
- id (String, PK) — Riot API champion key
- name (String)
- cost (Integer) — 1~5
- traits (JSONB) — 시너지 목록
- best_items (JSONB) — BIS 3종 + 대체 2종
- item_reasoning (JSONB) — 아이템별 추천 이유 (AI 생성)
- image_url (String) — Community Dragon 챔피언 초상화 URL
- splash_url (String) — 챔피언 스플래시 아트 URL (상세 화면 헤더용)

### items 테이블
- id (String, PK)
- name (String)
- description (Text)
- components (JSONB) — 재료 아이템 2종 ID
- image_url (String) — Data Dragon 아이템 아이콘 URL
- is_component (Boolean)

### augments 테이블
- id (String, PK)
- name (String)
- tier (Enum: Silver/Gold/Prismatic)
- description (Text)
- image_url (String) — Community Dragon 증강 아이콘 URL (Data Dragon에 없음)
- comp_synergy (JSONB) — 궁합 좋은 컴프 ID + 시너지 이유

### match_raw 테이블
- match_id (String, PK)
- region (String)
- participants (JSONB) — 전체 참가자 데이터
- patch_version (String)
- collected_at (Timestamp)

---

## 3. 환경변수 (.env.example)

RIOT_API_KEY=
DATABASE_URL=postgresql+asyncpg://tft_user:password@localhost:5432/tft_meta
REDIS_URL=redis://localhost:6379
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
PATCH_VERSION=14.x
SLACK_WEBHOOK_URL=

# K3s 배포 시 아래 값으로 교체됨
# DATABASE_URL=postgresql+asyncpg://tft_user:password@postgres-svc:5432/tft_meta
# REDIS_URL=redis://redis-svc:6379

---

## 4. Dockerfile (backend/Dockerfile)

K3s에서 사용할 컨테이너 이미지를 작성하라.

- 베이스: python:3.11-slim
- 작업 디렉터리: /app
- requirements.txt 먼저 복사 후 설치 (레이어 캐시 최적화)
- 비루트 유저(appuser) 생성 및 실행
- 헬스체크: GET /health 30초 간격
- 포트: 8000
- 실행: uvicorn app.main:app --host 0.0.0.0 --port 8000

멀티스테이지 빌드는 불필요, 단순 구조로 작성하라.

---

## 5. Riot API 서비스 (services/riot_api.py)

다음 함수를 async/await로 구현하라:
- get_challenger_summoners(region) — 챌린저 소환사 목록
- get_master_summoners(region) — 마스터 소환사 목록
- get_match_ids(puuid, count=20) — 최근 매치 ID 목록
- get_match_detail(match_id, region) — 매치 상세 데이터

Rate limit: asyncio.Semaphore(10)으로 동시 요청 제한,
100req/2min 초과 시 자동 sleep 후 재시도.
지원 리전: kr, na1, euw1

---

## 6. FastAPI API 엔드포인트

GET /health — 헬스체크 (K3s liveness probe용, DB 연결 상태 포함)
GET /api/v1/comps — 전체 추천 컴프 목록 (티어순, Redis 30분 캐시)
  쿼리 파라미터: tier(optional), limit(default 20)
GET /api/v1/comps/{comp_id} — 컴프 상세
GET /api/v1/comps/{comp_id}/board — 배치 보드 렌더링 데이터
GET /api/v1/champions — 전체 챔피언 + 아이템 가이드
GET /api/v1/augments — 증강 목록 (comp_id 필터 지원)
GET /api/v1/meta/summary — 오늘의 AI 메타 요약 (Redis 6시간 캐시)

모든 응답은 Pydantic v2 스키마로 정의하라.
CORS: Flutter Web과 K3s Ingress 도메인 허용.

---

## 7. docker-compose.yml (로컬 개발 전용)

서비스: api(FastAPI 8000), db(PostgreSQL 15), redis(Redis 7)
Airflow는 STEP 2에서 추가.
볼륨: postgres_data, redis_data (로컬 개발 데이터 유지)

---

## 완료 조건 체크리스트
- [ ] docker-compose up 으로 로컬 스택 실행 가능
- [ ] GET /health 200 응답 + DB 연결 상태 포함
- [ ] GET /api/v1/comps 더미 데이터 3개 이상 반환
- [ ] alembic upgrade head 마이그레이션 성공
- [ ] python test_riot_api.py 실행 시 매치 ID 목록 출력
- [ ] docker build -t tft-meta-api ./backend 이미지 빌드 성공
- [ ] README.md 로컬 실행 방법 작성 완료

Python 3.11, FastAPI 0.110+, SQLAlchemy 2.0+, Pydantic v2 사용.
모든 DB 접근은 async session으로 작성하라.
```

---

## STEP 2 — 데이터 파이프라인 & AI 분석 엔진

```
STEP 1이 완료된 상태에서 진행한다.
현재 프로젝트 구조를 먼저 확인하고 진행해줘.

## STEP 2 작업 목표
매일 자동으로 TFT 매치 데이터를 수집하고 AI로 분석하는 파이프라인을 완성한다.
Airflow도 K3s에 배포할 것이므로 컨테이너 환경에서 동작하도록 설계한다.

---

## 1. Airflow DAG (pipeline/airflow_dag.py)

DAG 이름: tft_daily_meta_update
실행 시간: 매일 19:00 UTC (04:00 KST)

태스크 의존성 순서:
sync_images → fetch_matches → parse_matches → cluster_comps → calculate_stats
  → generate_ai_summary → update_cache → send_push_notification

sync_images는 패치 버전이 변경된 경우에만 실제 동작하고,
변경 없으면 skip으로 처리하여 불필요한 API 호출을 방지한다.

각 태스크: 실패 시 최대 2회 재시도, 재시도 간격 5분.
전체 파이프라인 타임아웃: 3시간.

K3s 배포 시 KubernetesPodOperator 사용을 고려하여
각 태스크를 독립적인 Python 함수로 분리해 작성하라.

---

## 2. 이미지 동기화 서비스 (services/image_sync.py)

TFT 게임 내 이미지를 두 소스에서 수집하여 DB에 URL로 저장한다.
이미지 파일 자체는 저장하지 않고 URL만 관리한다 (CDN 직접 참조).

### 이미지 소스

**Data Dragon** (Riot 공식)
- 베이스 URL: https://ddragon.leagueoflegends.com/cdn/{version}
- 현재 버전 조회: https://ddragon.leagueoflegends.com/api/versions.json (첫 번째 값)
- 챔피언 목록 + 기본 이미지: /data/ko_KR/tft-champion.json
- 아이템 목록 + 이미지:      /data/ko_KR/tft-item.json
- 이미지 경로: /img/tft-champion/{id}.png / /img/tft-item/{id}.png

**Community Dragon** (비공식, 증강 및 고화질 자산)
- 베이스 URL: https://raw.communitydragon.org/latest
- TFT 증강 목록: /plugins/rcp-be-lol-game-data/global/default/v1/tftaugments.json
- 증강 이미지:   /game/{icon_path} (JSON 내 iconPath 필드를 소문자로 변환)
- 챔피언 고화질: /game/assets/characters/tft{id}/hud/tft{id}_square.tft_set{N}.png
- 트레이트 아이콘: /plugins/rcp-fe-lol-tft/global/default/assets/trait-icons/

### 구현할 함수

```python
async def sync_all_images(patch_version: str):
    """패치 버전 변경 시 전체 이미지 URL 동기화"""
    await sync_champion_images(patch_version)
    await sync_item_images(patch_version)
    await sync_augment_images()
    await sync_trait_icons()

async def sync_champion_images(patch_version: str):
    # Data Dragon에서 TFT 챔피언 목록 + 기본 image_url 수집
    # Community Dragon에서 고화질 초상화 URL → splash_url 로 저장
    # champions 테이블 upsert (id 기준)

async def sync_item_images(patch_version: str):
    # Data Dragon tft-item.json에서 아이템 목록 + image_url 수집
    # is_component 필드: 재료 아이템 여부 자동 판별 (from=[] 이면 재료)
    # items 테이블 upsert

async def sync_augment_images():
    # Community Dragon tftaugments.json에서 증강 목록 수집
    # iconPath를 실제 이미지 URL로 변환:
    #   "/lol-game-data/assets/..." → communitydragon URL로 치환
    # augments 테이블 upsert

async def check_patch_changed() -> bool:
    # Data Dragon versions.json의 최신 버전과 DB 저장 버전 비교
    # 다르면 True 반환 → DAG에서 sync_images 실행 결정
```

### 에러 처리
- Community Dragon 응답 실패 시 Data Dragon fallback URL 사용
- 이미지 URL 유효성 검사: HEAD 요청으로 404 확인 후 저장
- 동기화 완료 후 로그: "챔피언 {n}개, 아이템 {n}개, 증강 {n}개 동기화 완료"

### 수동 실행 CLI
  python -m services.image_sync --force   # 패치 변경 무관하게 강제 전체 동기화
  python -m services.image_sync --check   # 현재 패치 버전만 확인

---

## 2. 매치 수집 워커 (pipeline/fetch_matches.py)

수집 대상: KR, NA, EUW 리전의 마스터+ 소환사
소환사당 최근 10경기 매치 ID 수집.
이미 수집된 match_id는 스킵 (중복 방지).
목표: 리전당 5,000~10,000 매치/일.
동시 요청: asyncio.Semaphore(10)으로 제한.

수집 진행 상황 로그 출력: 리전별 수집 수, 스킵 수, 에러 수.
수집 완료 후 match_raw 테이블에 저장.

CLI 지원:
  python fetch_matches.py --region kr
  python fetch_matches.py --region kr --dry-run  (실제 저장 없이 카운트만)

---

## 3. 컴프 클러스터링 엔진 (pipeline/analyze_comps.py)

### 컴프 식별 알고리즘
1. 4위 이내 참가자의 챔피언 목록 추출
2. 코스트 4~5 챔피언을 "앵커"로 설정
3. 앵커 기준으로 자주 함께 등장하는 챔피언 조합 집계
4. 코사인 유사도 0.7 이상이면 같은 컴프로 분류
5. 샘플 수 50 미만 컴프는 제외
6. 최종 상위 20개 컴프 선정

### 레벨별 코어 챔피언 도출
레벨 6: 해당 컴프에서 레벨 6 시점에 가장 많이 보유한 챔피언 TOP 6
레벨 7: TOP 7 (전환 시 추가 챔피언 강조)
레벨 8: TOP 8 / 레벨 9: TOP 9

### 배치 좌표 도출
상위 10% 순위 참가자의 배치 데이터 평균을 내어
가장 빈번한 패턴을 7×4 그리드 좌표로 변환.

### 승률 계산
- win_rate: 1위 수 / 전체 게임 수
- top4_rate: 4위 이내 수 / 전체 게임 수
- avg_placement: 순위 합산 / 전체 게임 수
- play_rate: 해당 컴프 게임 수 / 전체 수집 게임 수

CLI 지원:
  python analyze_comps.py --date yesterday
  python analyze_comps.py --date 2024-01-15

---

## 4. AI 요약 생성 (services/ai_summary.py)

OpenRouter API + meta-llama/llama-3.3-70b-instruct:free 모델 사용.
OpenRouter는 OpenAI SDK와 호환되므로 base_url만 교체하여 사용한다.

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

# 모델: settings.OPENROUTER_MODEL (meta-llama/llama-3.3-70b-instruct:free)
```

HTTP 헤더에 다음을 추가하라 (OpenRouter 정책):
- HTTP-Referer: https://github.com/your-repo/tft-meta-advisor
- X-Title: TFT Meta Advisor

### 컴프별 전략 요약 프롬프트
system: "당신은 TFT 전문 코치입니다. 한국어로 간결하고 실용적인 전략 가이드를 작성하세요."

user 템플릿:
"다음 TFT 컴프 데이터를 분석하여 전략 가이드를 작성하세요.
컴프명: {name} / 승률: {win_rate}% / 평균 순위: {avg_placement}
코어 챔피언: {core_units} / 주요 시너지: {traits}

포함 항목:
1. 이 덱의 핵심 강점 (1~2문장)
2. 진입 조건 3가지 (각 1문장)
3. 주의할 약점 또는 카운터 (1문장)
총 150자 이내"

### 오늘의 메타 변화 요약
전날 대비 승률 변화 상위 5개 컴프를 분석.
system: "당신은 TFT 메타 분석가입니다."
user: "다음 메타 변화 데이터를 분석하여 오늘의 메타 요약을 한국어 3문장으로 작성하세요.
상승 컴프: {rising_comps} / 하락 컴프: {falling_comps} / 신규 등장: {new_comps}"

### free 티어 사용 시 주의사항
- meta-llama/llama-3.3-70b-instruct:free 는 rate limit이 있음
  (분당 20 req, 일 200 req 수준)
- 컴프 20개 + 메타 요약 1개 = 총 21 req/일 → free 티어로 충분
- rate limit 초과 시 429 응답, 자동 재시도 로직 구현 (최대 3회, 60초 간격)
- 추후 유료 모델로 교체 시 OPENROUTER_MODEL 환경변수만 변경하면 됨

---

## 5. 챔피언 아이템 추천 이유 생성 (services/item_reasoning.py)

ai_summary.py와 동일한 OpenRouter 클라이언트 재사용.

"{champion_name}에게 {item_name}이 왜 좋은지 20자 이내 한국어로 설명하세요.
예시: '공격속도와 AP 모두 시너지'"

챔피언 전체 처리 시 rate limit 주의: 요청 사이 3초 간격 sleep 적용.

---

## 6. 증강 분석 서비스 (services/augment_analyzer.py)

각 증강 + 컴프 조합의 평균 순위 변화를 계산.
스테이지별(2-1, 3-2, 4-2) 최적 증강 TOP 3 도출.

---

## 7. 에러 알림

파이프라인 태스크 실패 시 SLACK_WEBHOOK_URL로 알림 전송.
메시지 형식: "[TFT Pipeline] {task_name} 실패 - {error_message} ({timestamp})"

---

## 완료 조건 체크리스트
- [ ] python -m services.image_sync --force 실행 시 챔피언·아이템·증강 URL DB 저장 확인
- [ ] GET /api/v1/champions 응답의 image_url 필드가 실제 접근 가능한 URL인지 확인
- [ ] GET /api/v1/augments 응답의 image_url 필드가 Community Dragon URL인지 확인
- [ ] python fetch_matches.py --region kr --dry-run 실행 시 매치 ID 수 출력
- [ ] python analyze_comps.py --date yesterday 실행 시 comps 테이블에 20개 저장
- [ ] GET /api/v1/meta/summary 응답에 ai_summary 필드 포함
- [ ] Airflow UI에서 DAG 활성화 및 수동 트리거 성공 (sync_images 태스크 포함)
- [ ] 파이프라인 전체 실행 시간 2시간 이내 (로그 확인)
- [ ] 태스크 실패 시 Slack 웹훅 알림 수신
```

---

## STEP 3 — Flutter 앱 기본 UI 구현

```
STEP 1, 2가 완료된 상태에서 진행한다.
현재 프로젝트 구조를 먼저 확인하고 진행해줘.
백엔드 API가 http://localhost:8000 으로 실행 중이어야 한다.

## STEP 3 작업 목표
Flutter 앱의 핵심 화면 4개와 배치 보드 커스텀 렌더러를 구현한다.
Android / iOS / Web 모두 동작해야 한다.

---

## 1. 디렉터리 구조 생성

tft-meta-advisor/
└── flutter_app/
    ├── lib/
    │   ├── main.dart
    │   ├── core/
    │   │   ├── api_client.dart       # Dio 기반 HTTP 클라이언트
    │   │   ├── constants.dart        # 색상, 폰트, 상수
    │   │   ├── env_config.dart       # 환경별 API URL 설정
    │   │   ├── image_service.dart    # 이미지 URL 빌더 + 폴백 처리
    │   │   └── theme.dart            # 앱 테마 (다크 모드 기본)
    │   ├── models/
    │   │   ├── comp.dart
    │   │   ├── champion.dart
    │   │   └── augment.dart
    │   ├── providers/
    │   │   ├── comp_provider.dart    # Riverpod 컴프 상태관리
    │   │   └── meta_provider.dart    # 메타 요약 상태관리
    │   ├── screens/
    │   │   ├── home_screen.dart
    │   │   ├── comp_list_screen.dart
    │   │   ├── comp_detail_screen.dart
    │   │   └── champion_screen.dart
    │   └── widgets/
    │       ├── comp_card.dart
    │       ├── board_painter.dart    # CustomPainter
    │       ├── champion_icon.dart    # 이미지 로딩 + 코스트 테두리
    │       ├── item_icon.dart        # 이미지 로딩 + 폴백
    │       ├── augment_icon.dart     # 증강 이미지 + 티어 뱃지
    │       └── tier_badge.dart
    ├── pubspec.yaml
    └── assets/
        └── images/
            ├── placeholder_champion.png  # 챔피언 이미지 로딩 실패 시 폴백
            ├── placeholder_item.png      # 아이템 이미지 로딩 실패 시 폴백
            └── placeholder_augment.png   # 증강 이미지 로딩 실패 시 폴백

---

## 2. pubspec.yaml 의존성

flutter_riverpod: ^2.5.0
dio: ^5.4.0
cached_network_image: ^3.3.0   # 이미지 네트워크 로딩 + 자동 캐싱
go_router: ^13.0.0
shimmer: ^3.0.0
flutter_svg: ^2.0.0
hive_flutter: ^1.1.0

---

## 3. 이미지 서비스 (lib/core/image_service.dart)

API 응답의 image_url을 그대로 사용하되,
URL 오류 시 assets 폴백 이미지를 반환하는 헬퍼를 구현하라.

```dart
class ImageService {
  // 챔피언 초상화 위젯 반환
  // image_url이 null이거나 로딩 실패 시 placeholder_champion.png 표시
  static Widget championImage(String? imageUrl, {double size = 48}) {
    return CachedNetworkImage(
      imageUrl: imageUrl ?? '',
      width: size, height: size,
      fit: BoxFit.cover,
      placeholder: (_, __) => Shimmer.fromColors(...),  // 로딩 중 shimmer
      errorWidget: (_, __, ___) => Image.asset(
        'assets/images/placeholder_champion.png',
        width: size, height: size,
      ),
    );
  }

  // 아이템 아이콘 위젯
  static Widget itemImage(String? imageUrl, {double size = 28}) { ... }

  // 증강 아이콘 위젯
  static Widget augmentImage(String? imageUrl, {double size = 36}) { ... }

  // 트레이트(시너지) 아이콘 위젯
  static Widget traitIcon(String? imageUrl, {double size = 24}) { ... }
}
```

캐시 설정:
- CachedNetworkImage 기본 캐시 유지 (디스크 캐시 7일, 메모리 캐시 100개)
- 앱 재시작 후에도 이전에 로드한 이미지는 즉시 표시

---

## 4. 이미지 적용 위젯 구현

### ChampionIcon (widgets/champion_icon.dart)
```dart
// 챔피언 아이콘 = 육각형 클리핑 + 코스트별 테두리 + 이미지
Widget build(BuildContext context) {
  return Stack(children: [
    // 1. 코스트별 색상 테두리 육각형
    CustomPaint(painter: HexBorderPainter(color: costColor)),
    // 2. 육각형 클리핑된 챔피언 이미지
    ClipPath(
      clipper: HexClipper(),
      child: ImageService.championImage(champion.imageUrl, size: iconSize),
    ),
    // 3. 별 등급 오버레이 (우하단)
    Positioned(bottom: 2, right: 2,
      child: StarRatingWidget(stars: starLevel)),
    // 4. 아이템 슬롯 오버레이 (하단 3칸)
    Positioned(bottom: -8,
      child: ItemSlotRow(items: champion.equippedItems)),
  ]);
}
```

### ItemIcon (widgets/item_icon.dart)
```dart
// 아이템 아이콘 = 둥근 사각형 + 이미지 + 탭 시 툴팁
// 툴팁: 아이템명 + 재료 조합 (재료 아이콘 2개 + "+" 표시)
Widget build(BuildContext context) {
  return GestureDetector(
    onLongPress: () => showItemTooltip(context, item),
    child: Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.grey.shade600),
      ),
      child: ImageService.itemImage(item.imageUrl, size: itemSize),
    ),
  );
}
```

### AugmentIcon (widgets/augment_icon.dart)
```dart
// 증강 아이콘 = 티어별 육각형 프레임 + Community Dragon 이미지
// Silver: 회색 프레임 / Gold: 황금 프레임 / Prismatic: 무지개 그라디언트 프레임
Widget build(BuildContext context) {
  return Stack(children: [
    CustomPaint(painter: AugmentFramePainter(tier: augment.tier)),
    ImageService.augmentImage(augment.imageUrl, size: augmentSize),
  ]);
}
```

---

## 3. 환경별 API URL 설정 (lib/core/env_config.dart)

const String env = String.fromEnvironment('ENV', defaultValue: 'development');

빌드 시 주입:
- development: http://localhost:8000
- production:  https://api.tft-meta.example.com  ← K3s Ingress 도메인

flutter run --dart-define=ENV=development
flutter build apk --dart-define=ENV=production

---

## 4. 앱 테마 (다크 모드 기본, theme.dart)

색상 팔레트:
- primary:    Color(0xFF1A4B8C)  — TFT 브랜드 블루
- accent:     Color(0xFF2E86DE)  — 액센트 블루
- background: Color(0xFF0F1923)  — 진한 네이비 (다크 배경)
- surface:    Color(0xFF1C2A3A)  — 카드 배경
- gold:       Color(0xFFCDA855)  — 5코스트 / S티어 색상

챔피언 코스트별 테두리 색상 (constants.dart에 Map으로 정의):
1코스트: #808080, 2코스트: #2EA94E, 3코스트: #2277BE,
4코스트: #9B4FC4, 5코스트: #CDA855

---

## 5. 홈 화면 (home_screen.dart)

### 앱바
- 앱 로고 + "TFT Meta Advisor"
- 현재 패치 버전 서브텍스트

### 메타 요약 배너
- AI 생성 오늘의 메타 요약 텍스트
- 접힘/펼침 토글 애니메이션
- "오늘 07:00 업데이트" 갱신 시각 표시

### 추천 컴프 TOP 5 섹션
- CompCard 위젯 세로 스크롤 목록 5개
- "전체 보기" 버튼 → comp_list_screen 이동

### CompCard 위젯 레이아웃
┌────────────────────────────────┐
│ [S] 이렐리아 전사      승률 18.3% │
│ [🧙][⚔️][🛡️][🏹][🔮]           │  ← 챔피언 아이콘 (코스트별 테두리색)
│ 평균 순위 3.21   픽률 8.4%  [>] │
└────────────────────────────────┘

---

## 6. 컴프 목록 화면 (comp_list_screen.dart)

- 상단 필터 탭: 전체 / S티어 / A티어 / B티어
- 검색바: 컴프명 또는 챔피언명 필터링
- 정렬 옵션: 승률순 / 픽률순 / 평균순위순
- 무한 스크롤 (20개씩 페이징)
- 각 항목은 CompCard 위젯 재사용

---

## 7. 컴프 상세 화면 (comp_detail_screen.dart)

TabBar 구조로 4개 탭 구현:

### 탭 1: 배치
- BoardPainter 위젯 (7×4 그리드)
- 레벨 선택 드롭다운: 6 / 7 / 8 / 9
- 레벨 선택 시 해당 레벨 코어 챔피언 황금 테두리 강조
- 빈 슬롯: 회색 점선 육각형

### 탭 2: 아이템
- 챔피언별 행: 챔피언 아이콘 + BIS 아이템 3개 + 추천 이유 텍스트
- 아이템 탭 시 재료 조합법 툴팁 팝업

### 탭 3: 증강
- 스테이지 탭: 2-1 / 3-2 / 4-2
- 추천 증강 TOP 3: 증강 이미지 + 이름 + 효과 요약 + 시너지 이유

### 탭 4: 진입조건
- 진입 조건 카드 목록 (아이콘 + 텍스트)
- AI 생성 전략 요약 전문
- 카운터 컴프 경고 섹션

---

## 9. 배치 보드 CustomPainter (board_painter.dart)

7열 × 4행 육각형 그리드를 Canvas로 직접 그려라.

각 육각형:
- 크기: 가로 60px
- 챔피언 없는 슬롯: 회색(#3A3A3A) 점선 테두리 육각형
- 챔피언 있는 슬롯: 코스트별 색상 테두리 + 챔피언 이미지 클리핑
  → champion.imageUrl을 CachedNetworkImage로 로드 후 ui.Image로 변환하여 Canvas에 drawImage
  → 이미지 로드 전: 코스트 색상 단색 원형으로 표시 (shimmer 효과)
- 아이템: 챔피언 하단 우측에 24px 크기로 최대 3개 오버레이
  → item.imageUrl을 동일 방식으로 Canvas에 렌더링
- 별 등급: 챔피언 상단에 별 아이콘 (기본 2스타, 3스타는 노란색 강조)

Canvas에서 네트워크 이미지 사용 방법:
```dart
// CustomPainter에서 이미지를 쓰려면 ui.Image 타입이 필요
// 미리 로드 후 상태로 관리
Future<ui.Image> loadImage(String url) async {
  final completer = Completer<ui.Image>();
  final imageProvider = CachedNetworkImageProvider(url);
  imageProvider.resolve(ImageConfiguration())
    .addListener(ImageStreamListener((info, _) =>
      completer.complete(info.image)));
  return completer.future;
}
```

입력: List<BoardPosition> (row, col, championId, imageUrl, items, starLevel)
레벨 변경 시 AnimatedContainer로 부드럽게 전환.

---

## 완료 조건 체크리스트
- [ ] flutter run -d chrome 웹 빌드 정상 실행
- [ ] flutter run -d android Android 빌드 정상 실행
- [ ] 홈 화면 CompCard에 챔피언 실제 초상화 이미지 표시 (shimmer → 이미지 전환)
- [ ] 컴프 상세 아이템 탭에 아이템 아이콘 실제 이미지 표시
- [ ] 컴프 상세 증강 탭에 증강 아이콘 실제 이미지 + 티어별 프레임 표시
- [ ] 배치 보드 7×4 격자에 챔피언 초상화 + 아이템 아이콘 실제 이미지 렌더링
- [ ] 이미지 로딩 실패 시 placeholder 이미지 표시 (네트워크 차단 테스트)
- [ ] 레벨 6→7→8→9 전환 시 챔피언 강조 변경
- [ ] 탭 전환 부드러운 애니메이션 확인
- [ ] --dart-define=ENV=production 빌드 시 K3s API URL 사용 확인
- [ ] flutter test 위젯 테스트 통과 (CompCard, TierBadge, ChampionIcon, ItemIcon)
```

---

## STEP 4 — Android 플로팅 버블 오버레이 & iOS 최적화

```
STEP 1~3이 완료된 상태에서 진행한다.
현재 프로젝트 구조를 먼저 확인하고 진행해줘.
Flutter 앱이 Android와 iOS에서 정상 실행되어야 한다.

## STEP 4 작업 목표
롤체지지/닥지지 스타일의 플로팅 버블 오버레이를 구현한다.
- Android: flutter_overlay_window 기반 플로팅 버블
- iOS: 앱 전환 최적화 + Live Activities + 홈 화면 위젯

---

## Android 플로팅 버블 오버레이

### 1. 패키지 추가 (pubspec.yaml)
flutter_overlay_window: ^0.4.0

### 2. Android 퍼미션 설정 (AndroidManifest.xml)
<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>
<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>

### 3. 오버레이 파일 구조 생성

lib/overlay/
├── overlay_entry.dart      # 오버레이 진입점 (@pragma vm:entry-point 필수)
├── overlay_screen.dart     # 오버레이 UI
├── overlay_provider.dart   # 오버레이 상태관리
└── overlay_controller.dart # 오버레이 제어

### 4. 오버레이 UI 상태 구현 (overlay_screen.dart)

#### 버블 상태 (기본)
- 크기: 56×56dp 원형
- 콘텐츠: 앱 로고 아이콘
- 위치: 화면 우측 중앙 (기본), GestureDetector 드래그로 이동 가능
- 불투명도: 0.85
- 드래그 종료 시 위치를 SharedPreferences에 저장

#### 미니 패널 상태 (버블 탭 시 팝업)
┌─────────────────────────┐
│ [컴프1 탭][컴프2 탭][컴프3 탭] │  ← 즐겨찾기 컴프 전환 탭 (최대 3개)
├─────────────────────────┤
│ 이렐리아 전사    승률 18% │
│ [🖼챔피언1][🖼챔피언2][🖼챔피언3] │  ← 실제 챔피언 초상화 이미지 (32px)
│ 레벨: [6][7][8][9]      │
├─────────────────────────┤
│ BIS: [🖼아이템1][🖼아이템2][🖼아이템3] │  ← 실제 아이템 아이콘 이미지 (24px)
├─────────────────────────┤
│ 추천증강: [🖼증강아이콘] 증강이름 │  ← 실제 증강 아이콘 이미지 (24px)
│ [닫기]       [앱 열기]  │
└─────────────────────────┘
너비: 280dp, 배경 Color(0xE61C2A3A) (반투명)

오버레이는 메모리 제약이 있으므로 이미지 크기를 작게 유지하라:
- 챔피언: 32px (일반 화면 48px보다 작게)
- 아이템/증강: 24px
- CachedNetworkImage 사용, 오버레이 전용 캐시 크기 제한: 최대 20개

### 5. 오버레이 컨트롤러 (overlay_controller.dart)

class OverlayController {
  Future<bool> requestPermission();        // SYSTEM_ALERT_WINDOW 권한 요청
  Future<void> startOverlay();             // 오버레이 시작
  Future<void> stopOverlay();              // 오버레이 종료
  void updateFavoriteComps(List<Comp> comps); // 즐겨찾기 컴프 전달
}

### 6. 권한 요청 화면 (screens/overlay_setup_screen.dart)

- 최초 실행 시 안내 화면
- "권한 허용" 버튼 → 설정 화면 이동
- 권한 거부 시 오버레이 기능 비활성화 안내

### 7. 메인 앱 홈 화면 수정 (home_screen.dart)

- 우측 하단 FAB: "게임 오버레이 시작" 버튼
- 오버레이 활성 시 AppBar에 녹색 점(●) 표시
- 컴프 상세에서 별(★) 탭 시 즐겨찾기 등록 (최대 3개)

---

## iOS 최적화

### 8. 빠른 앱 복원 (lib/core/app_state_manager.dart)

앱 백그라운드 전환 시 마지막 컴프 ID + 레벨 저장 (SharedPreferences)
포그라운드 복귀 시 즉시 복원. 목표: 콜드 스타트 1.5초 이내.

### 9. iOS 홈 화면 위젯 (ios/TFTWidget/ — Swift, WidgetKit)

Small: Top 1 컴프 이름 + 승률 + 챔피언 아이콘 3개
Medium: Top 3 컴프 목록 + 각 승률 + 티어 뱃지
App Group으로 Flutter ↔ Widget 간 UserDefaults 공유.

Flutter 플랫폼 채널:
// lib/platform/widget_channel.dart
static const channel = MethodChannel('tft_meta/widget');
Future<void> updateWidgetData(List<Comp> topComps);

### 10. Live Activities (ios/LiveActivity/ — Swift, ActivityKit)

Compact: 컴프 아이콘 / 다음 구매 챔피언 이름
Expanded: 컴프명 + 코어 챔피언 3종 아이콘 + 현재 레벨

Flutter 플랫폼 채널:
// lib/platform/live_activity_channel.dart
static const channel = MethodChannel('tft_meta/live_activity');
Future<void> startActivity(Comp comp, int level);
Future<void> updateActivity(int level);
Future<void> stopActivity();

---

## 완료 조건 체크리스트
- [ ] Android: 버블 아이콘이 TFT 앱 위에 표시
- [ ] Android: 버블 탭 시 미니 패널 팝업 (슬라이드 애니메이션)
- [ ] Android: 패널 레벨 버튼 탭 시 챔피언 목록 변경
- [ ] Android: 즐겨찾기 3개 컴프 탭 전환
- [ ] Android: 드래그 후 재시작 시 마지막 위치 유지
- [ ] iOS: 홈 화면 위젯 추가 가능 확인
- [ ] iOS: 앱 전환 후 1.5초 이내 마지막 화면 복원
- [ ] iOS: Live Activities 잠금화면 표시 확인
```

---

## STEP 5 — K3s 배포 + 오프라인 지원 + 외부 접근 설정

```
STEP 1~4가 완료된 상태에서 진행한다.
현재 프로젝트 구조를 먼저 확인하고 진행해줘.

## 배포 환경
- 단일 노드 K3s (개인 PC, Linux)
- 전체 스택 K3s 운영: FastAPI, PostgreSQL, Redis, Airflow
- 외부 접근: 공인 IP 또는 도메인으로 집 밖에서도 API 사용 가능
- K3s 기본 내장 Traefik Ingress Controller 활용

## STEP 5 작업 목표
K3s 매니페스트 전체 작성, 외부 접근 설정, 오프라인 지원, 푸시 알림, 최종 빌드.

---

## 1. K3s 네임스페이스 및 공통 설정

### k8s/namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tft-meta
```

### k8s/secrets.yaml (Secret 생성 방법 안내 포함)
민감 정보는 kubectl로 직접 생성하는 명령어를 주석으로 안내하라:

kubectl create secret generic tft-secrets \
  --from-literal=database-url='postgresql://tft_user:password@postgres-svc:5432/tft_meta' \
  --from-literal=redis-url='redis://redis-svc:6379' \
  --from-literal=riot-api-key='YOUR_KEY' \
  --from-literal=openrouter-api-key='YOUR_KEY' \
  --from-literal=openrouter-model='meta-llama/llama-3.3-70b-instruct:free' \
  -n tft-meta

Secret을 yaml로도 작성하되 실제 값은 base64 플레이스홀더로 남겨라.

---

## 2. PostgreSQL 배포 (k8s/postgres/)

### postgres-pvc.yaml
- 단일 노드이므로 storageClassName: local-path (K3s 기본 제공)
- 용량: 10Gi
- accessModes: ReadWriteOnce

### postgres-deployment.yaml
- image: postgres:15-alpine
- 환경변수: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD (Secret에서 주입)
- volumeMount: /var/lib/postgresql/data → PVC
- resources:
    requests: { memory: "256Mi", cpu: "250m" }
    limits:   { memory: "512Mi", cpu: "500m" }
- livenessProbe: pg_isready -U tft_user 30초 간격

### postgres-service.yaml
- type: ClusterIP (외부 노출 불필요)
- name: postgres-svc
- port: 5432

---

## 3. Redis 배포 (k8s/redis/)

### redis-pvc.yaml
- storageClassName: local-path
- 용량: 2Gi

### redis-deployment.yaml
- image: redis:7-alpine
- 커맨드: redis-server --appendonly yes (AOF 영속성)
- volumeMount: /data → PVC
- resources:
    requests: { memory: "128Mi", cpu: "100m" }
    limits:   { memory: "256Mi", cpu: "200m" }

### redis-service.yaml
- type: ClusterIP
- name: redis-svc
- port: 6379

---

## 4. FastAPI 배포 (k8s/api/)

### api-deployment.yaml
- image: tft-meta-api:latest (로컬 빌드 이미지, imagePullPolicy: Never)
- replicas: 1 (단일 노드, 리소스 절약)
- 환경변수: Secret에서 DATABASE_URL, REDIS_URL, RIOT_API_KEY, OPENROUTER_API_KEY, OPENROUTER_MODEL 주입
- resources:
    requests: { memory: "256Mi", cpu: "250m" }
    limits:   { memory: "512Mi", cpu: "1000m" }
- livenessProbe:  GET /health 30초 간격, 초기 지연 15초
- readinessProbe: GET /health 10초 간격

### api-service.yaml
- type: ClusterIP
- name: api-svc
- port: 80 → targetPort: 8000

---

## 5. Airflow 배포 (k8s/airflow/)

Airflow를 단일 노드 K3s에서 경량으로 운영하기 위해
공식 Helm Chart 대신 직접 매니페스트로 작성하라.
(SequentialExecutor 사용 — 단일 노드 환경에 적합)

### airflow-pvc.yaml
- dags-pvc: 1Gi (DAG 파일 저장)
- logs-pvc: 5Gi (로그 저장)
- storageClassName: local-path

### airflow-configmap.yaml
다음 Airflow 설정을 ConfigMap으로 관리:
- AIRFLOW__CORE__EXECUTOR: SequentialExecutor
- AIRFLOW__CORE__LOAD_EXAMPLES: "False"
- AIRFLOW__WEBSERVER__EXPOSE_CONFIG: "True"
- AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL: "60"

### airflow-deployment.yaml
webserver와 scheduler를 하나의 Pod에 묶어서 실행 (단일 노드 경량화).
image: apache/airflow:2.9-python3.11
두 컨테이너 (webserver, scheduler)를 같은 Pod에 배치.
dags-pvc를 /opt/airflow/dags에 마운트.
DAG 파일 동기화: git-sync 사이드카 컨테이너 또는 initContainer로
GitHub 레포에서 DAG 파일을 주기적으로 pull하는 방식 구현.

### airflow-service.yaml
- type: ClusterIP
- name: airflow-svc
- port: 8080 (Airflow 웹 UI)

### Airflow DB 초기화 Job (airflow-init-job.yaml)
- airflow db migrate 실행
- airflow users create (admin 계정 생성)
- completions: 1, restartPolicy: OnFailure

---

## 6. Ingress 설정 (k8s/ingress/)

K3s 기본 내장 Traefik을 활용하여 외부 접근을 설정한다.

### ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tft-meta-ingress
  namespace: tft-meta
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    # Let's Encrypt TLS 자동 발급 (cert-manager 설치 후)
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.tft-meta.example.com   # ← 실제 도메인으로 교체
      secretName: tft-meta-tls
  rules:
    - host: api.tft-meta.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port:
                  number: 80
    - host: airflow.tft-meta.example.com  # Airflow UI 외부 접근
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: airflow-svc
                port:
                  number: 8080
```

### cert-manager 설치 안내 (k8s/ingress/cert-manager-setup.md)
다음 명령어로 cert-manager를 K3s에 설치하는 방법을 문서화하라:

# cert-manager 설치
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# Let's Encrypt ClusterIssuer 생성 (이메일 주소 교체 필요)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: traefik

Let's Encrypt는 공인 IP에서 도메인이 연결되어 있어야 발급된다.
도메인 없이 테스트할 경우 NodePort로 대체하는 방법도 함께 안내하라.

---

## 7. 이미지 빌드 및 K3s 로드 스크립트 (scripts/deploy.sh)

단일 노드이므로 레지스트리 없이 이미지를 직접 K3s에 주입한다.

#!/bin/bash
# TFT Meta Advisor K3s 배포 스크립트

set -e

echo "=== 1. Docker 이미지 빌드 ==="
docker build -t tft-meta-api:latest ./backend

echo "=== 2. K3s containerd에 이미지 주입 ==="
# K3s는 Docker 데몬을 사용하지 않으므로 직접 import 필요
docker save tft-meta-api:latest | sudo k3s ctr images import -

echo "=== 3. 네임스페이스 생성 ==="
kubectl apply -f k8s/namespace.yaml

echo "=== 4. 스토리지(PVC) 생성 ==="
kubectl apply -f k8s/postgres/postgres-pvc.yaml
kubectl apply -f k8s/redis/redis-pvc.yaml
kubectl apply -f k8s/airflow/airflow-pvc.yaml

echo "=== 5. ConfigMap 적용 ==="
kubectl apply -f k8s/airflow/airflow-configmap.yaml

echo "=== 6. 데이터베이스 배포 (PostgreSQL, Redis) ==="
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/

echo "=== 7. PostgreSQL 준비 대기 ==="
kubectl wait --for=condition=ready pod -l app=postgres -n tft-meta --timeout=120s

echo "=== 8. API 서버 배포 ==="
kubectl apply -f k8s/api/

echo "=== 9. Airflow 초기화 Job 실행 ==="
kubectl apply -f k8s/airflow/airflow-init-job.yaml
kubectl wait --for=condition=complete job/airflow-init -n tft-meta --timeout=180s

echo "=== 10. Airflow 배포 ==="
kubectl apply -f k8s/airflow/

echo "=== 11. Ingress 적용 ==="
kubectl apply -f k8s/ingress/

echo "=== 배포 완료 ==="
kubectl get pods -n tft-meta
kubectl get ingress -n tft-meta

업데이트 배포 스크립트 (scripts/update-api.sh)도 별도로 작성:
이미지 재빌드 → K3s import → kubectl rollout restart deployment/api -n tft-meta

---

## 8. 오프라인 지원 (lib/core/offline_cache.dart)

Hive 패키지로 로컬 캐시 구현:

캐시 정책:
- 컴프 목록: 마지막 성공 응답 저장, TTL 24시간
- 컴프 상세: 조회한 데이터 저장, TTL 24시간
- 메타 요약: 마지막 요약 저장, TTL 24시간

네트워크 없을 때 자동으로 캐시 데이터 사용 후
앱 상단에 배너 표시: "오프라인 모드 — 07:00 기준 데이터"

Hive Box 구조:
- comps_box: comp_id → Comp JSON
- meta_box: 'summary' → MetaSummary JSON
- cache_meta_box: key → 저장 시각 (TTL 계산용)

---

## 9. 푸시 알림 (FCM)

### 백엔드 (backend/services/push_notification.py)
Firebase Admin SDK 사용.

알림 유형 3가지:
1. 메타 갱신 알림: 제목 "TFT 메타 업데이트" / 내용 "오늘의 메타가 분석 완료되었습니다 🎯"
2. 패치 감지 알림: 제목 "새 패치 {version}" / 내용 "메타 분석이 완료되었습니다!"
3. 즐겨찾기 컴프 티어 변동: 제목 "메타 변화 알림" / 내용 "{컴프명}이 S티어로 올라섰습니다 ⬆️"

토픽 구조: meta_update, patch_alert, comp_{comp_id}
Airflow DAG의 send_push_notification 태스크에서 호출.

### Flutter (lib/services/notification_service.dart)
firebase_messaging 패키지 사용.
포그라운드 알림 처리 (flutter_local_notifications)
알림 탭 시 딥링크: meta_update → 홈, comp_{id} → 컴프 상세 화면

---

## 10. Flutter Web PWA 최적화

web/manifest.json: name, short_name, display: standalone,
background_color: #0F1923, theme_color: #1A4B8C

Service Worker:
- API 응답: Network first, 실패 시 캐시 폴백
- 이미지: Cache first
- 오프라인 폴백: /offline.html

빌드: flutter build web --web-renderer canvaskit --release

---

## 11. 분석 & 에러 트래킹

Firebase Analytics 이벤트:
- comp_viewed, overlay_opened, overlay_comp_switched
- favorite_added, level_changed, board_tab_viewed

Sentry: SentryFlutter.init, 오버레이 에러에 태그 'overlay: true' 추가.

---

## 12. 최종 QA 체크리스트

### K3s 배포 검증
- [ ] kubectl get pods -n tft-meta 전체 Running 상태
- [ ] kubectl get ingress -n tft-meta Ingress 정상 등록
- [ ] 외부 도메인으로 GET /health 200 응답 (HTTPS)
- [ ] GET /api/v1/comps 외부에서 정상 응답
- [ ] Airflow 웹 UI 외부 도메인으로 접근 가능
- [ ] Airflow DAG 수동 트리거 성공 (K3s 환경에서)
- [ ] scripts/deploy.sh 처음부터 끝까지 에러 없이 실행
- [ ] scripts/update-api.sh 실행 후 롤링 업데이트 확인

### 기능 검증
- [ ] 홈 화면 메타 요약 + Top 5 컴프 정상 표시
- [ ] 배치 보드 레벨 6/7/8/9 전환
- [ ] Android: 오버레이 버블 → 패널 전체 플로우
- [ ] iOS: 홈 화면 위젯 갱신
- [ ] 오프라인 모드 캐시 데이터 표시 + 배너
- [ ] 푸시 알림 수신 → 딥링크 이동

### 성능 검증
- [ ] K3s Pod 메모리 사용량 확인 (kubectl top pods -n tft-meta)
- [ ] 홈 화면 콜드 스타트 3초 이내
- [ ] 오버레이 패널 열기 0.3초 이내

### 앱 빌드
- [ ] flutter build appbundle --dart-define=ENV=production 에러 없음
- [ ] flutter build ipa --dart-define=ENV=production 에러 없음
- [ ] flutter build web --dart-define=ENV=production 에러 없음

### 문서화
- [ ] README.md: K3s 배포 방법 (scripts/deploy.sh 사용법) 작성
- [ ] README.md: 도메인 설정 및 cert-manager 설치 방법 작성
- [ ] CHANGELOG.md: v1.0.0 릴리즈 노트
- [ ] .env.example: K3s 환경변수 주석 포함
```

---

## K3s 운영 참고 명령어

```bash
# 전체 스택 상태 확인
kubectl get all -n tft-meta

# Pod 로그 확인
kubectl logs -f deployment/api -n tft-meta
kubectl logs -f deployment/airflow -n tft-meta -c scheduler

# Pod 재시작
kubectl rollout restart deployment/api -n tft-meta

# API 이미지 업데이트 (코드 변경 후)
bash scripts/update-api.sh

# DB 접속 (디버깅용)
kubectl exec -it deployment/postgres -n tft-meta -- psql -U tft_user -d tft_meta

# Redis 접속 (디버깅용)
kubectl exec -it deployment/redis -n tft-meta -- redis-cli

# 리소스 사용량 모니터링
kubectl top pods -n tft-meta
kubectl top nodes

# Airflow DAG 수동 트리거
kubectl exec -it deployment/airflow -n tft-meta -c scheduler -- \
  airflow dags trigger tft_daily_meta_update

# 전체 스택 삭제 (초기화)
kubectl delete namespace tft-meta
```

---

> **팁**: 각 STEP 시작 시 프롬프트 앞에 아래 문장을 추가하면 Claude Code가 더 정확하게 동작합니다.
>
> `"현재 프로젝트 구조를 ls -R로 확인하고, 기존 파일과 충돌 없이 진행해줘."`
>
> **K3s 주의사항**: 단일 노드 환경이므로 Pod가 재시작될 때 PVC 데이터는 유지되지만,
> PC를 재부팅하면 K3s가 자동 시작되도록 `sudo systemctl enable k3s` 설정을 확인하세요.
