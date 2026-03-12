"""
Airflow DAG: tft_daily_meta_update

목적:
  매일 KR/NA/EUW 리전의 마스터+ 매치 데이터를 수집하고,
  컴프 클러스터링 → 통계 계산 → AI 요약 생성 → 캐시 갱신 → Slack 알림 순으로 실행.

스케줄: 19:00 UTC (04:00 KST)
전체 타임아웃: 3시간
태스크 실패 시 최대 2회 재시도, 간격 5분.

태스크 의존성:
  fetch_matches → parse_matches → cluster_comps → calculate_stats
    → generate_ai_summary → update_cache → send_push_notification

K3s 환경에서는 각 태스크 함수가 KubernetesPodOperator의 entrypoint로 독립 실행될 수 있도록
각 callable을 독립적인 Python 함수로 분리한다.
"""
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "tft-meta-advisor",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "on_failure_callback": None,  # Slack 콜백은 태스크 내부에서 처리
}

REGIONS = ["kr", "na1", "euw1"]


# ---------------------------------------------------------------------------
# Task callables — 각 함수는 KubernetesPodOperator entrypoint로도 동작 가능하도록
# asyncio.run() 래퍼를 포함한다.
# ---------------------------------------------------------------------------

def task_sync_images(**context) -> None:
    """패치 버전 변경 시 챔피언/아이템/증강 이미지 URL 동기화."""
    import asyncio

    from app.services.image_sync import check_patch_changed, sync_all_images
    from app.services.riot_api import get_latest_patch_version
    from app.services.slack_notifier import notify_failure

    try:
        if asyncio.run(check_patch_changed()):
            patch_version = asyncio.run(get_latest_patch_version())
            asyncio.run(sync_all_images(patch_version))
            logger.info("[sync_images] 이미지 동기화 완료")
        else:
            logger.info("[sync_images] 패치 변경 없음 — 동기화 스킵")
    except Exception as exc:
        asyncio.run(notify_failure("sync_images", str(exc)))
        raise


def task_fetch_matches(**context) -> None:
    """
    Riot API에서 KR/NA/EUW 마스터+ 매치 ID를 수집하고 match_raw 테이블에 저장.
    실행 날짜를 XCom에 push하여 후속 태스크가 날짜 범위 필터로 사용한다.
    """
    import asyncio

    from pipeline.fetch_matches import run as fetch_run
    from app.services.slack_notifier import notify_failure

    run_date: str = context["ds"]  # YYYY-MM-DD
    logger.info("[fetch_matches] 실행 날짜: %s", run_date)

    try:
        total = asyncio.run(fetch_run(regions=REGIONS))
        logger.info("[fetch_matches] 총 수집 매치: %d", total)
        context["ti"].xcom_push(key="run_date", value=run_date)
        context["ti"].xcom_push(key="total_fetched", value=total)
    except Exception as exc:
        asyncio.run(notify_failure("fetch_matches", str(exc)))
        raise


def task_parse_matches(**context) -> None:
    """
    match_raw 테이블의 원시 JSON에서 참가자 데이터를 파싱하고 정규화.
    후속 클러스터링을 위한 중간 집계(XCom)를 남긴다.
    """
    import asyncio

    from pipeline.fetch_matches import parse_raw_matches
    from app.services.slack_notifier import notify_failure

    run_date: str = context["ti"].xcom_pull(key="run_date", task_ids="fetch_matches")
    logger.info("[parse_matches] 날짜: %s", run_date)

    try:
        count = asyncio.run(parse_raw_matches(run_date=run_date))
        logger.info("[parse_matches] 파싱된 참가자 레코드: %d", count)
        context["ti"].xcom_push(key="participant_count", value=count)
    except Exception as exc:
        asyncio.run(notify_failure("parse_matches", str(exc)))
        raise


def task_cluster_comps(**context) -> None:
    """
    파싱된 참가자 데이터로 코사인 유사도 기반 컴프 클러스터링 실행.
    클러스터 결과를 임시 테이블(comp_clusters) 또는 XCom에 저장.
    """
    import asyncio

    from pipeline.analyze_comps import cluster_and_store
    from app.services.slack_notifier import notify_failure

    run_date: str = context["ti"].xcom_pull(key="run_date", task_ids="fetch_matches")
    logger.info("[cluster_comps] 날짜: %s", run_date)

    try:
        cluster_count = asyncio.run(cluster_and_store(run_date=run_date))
        logger.info("[cluster_comps] 클러스터 수: %d", cluster_count)
        context["ti"].xcom_push(key="cluster_count", value=cluster_count)
    except Exception as exc:
        asyncio.run(notify_failure("cluster_comps", str(exc)))
        raise


def task_calculate_stats(**context) -> None:
    """
    각 클러스터(컴프)에 대해 win_rate / top4_rate / avg_placement / play_rate 계산 후
    comps 테이블에 upsert.
    """
    import asyncio

    from pipeline.analyze_comps import calculate_and_upsert_stats
    from app.services.slack_notifier import notify_failure

    run_date: str = context["ti"].xcom_pull(key="run_date", task_ids="fetch_matches")
    logger.info("[calculate_stats] 날짜: %s", run_date)

    try:
        upserted = asyncio.run(calculate_and_upsert_stats(run_date=run_date))
        logger.info("[calculate_stats] upsert된 컴프 수: %d", upserted)
        context["ti"].xcom_push(key="upserted_count", value=upserted)
    except Exception as exc:
        asyncio.run(notify_failure("calculate_stats", str(exc)))
        raise


def task_generate_ai_summary(**context) -> None:
    """
    상위 컴프 각각에 대해 OpenRouter AI 전략 요약을 생성하고 comps.ai_summary 갱신.
    오늘의 메타 변화 요약도 생성한다.
    """
    import asyncio

    from pipeline.analyze_comps import generate_summaries_for_top_comps
    from app.services.slack_notifier import notify_failure

    run_date: str = context["ti"].xcom_pull(key="run_date", task_ids="fetch_matches")
    logger.info("[generate_ai_summary] 날짜: %s", run_date)

    try:
        updated = asyncio.run(generate_summaries_for_top_comps(run_date=run_date))
        logger.info("[generate_ai_summary] AI 요약 생성 완료: %d 컴프", updated)
    except Exception as exc:
        asyncio.run(notify_failure("generate_ai_summary", str(exc)))
        raise


def task_update_cache(**context) -> None:
    """
    Redis 캐시의 comps / meta-summary 키를 무효화하여 API가 신선한 데이터를 반환하도록 함.
    """
    import asyncio

    from app.services.cache import cache_delete
    from app.services.slack_notifier import notify_failure

    cache_keys = [
        "comps:list:all",
        "meta:summary",
        "augments:analysis",
    ]

    async def _invalidate() -> None:
        for key in cache_keys:
            await cache_delete(key)
            logger.info("[update_cache] 캐시 삭제: %s", key)

    try:
        asyncio.run(_invalidate())
        logger.info("[update_cache] 캐시 무효화 완료")
    except Exception as exc:
        asyncio.run(notify_failure("update_cache", str(exc)))
        raise


def task_send_push_notification(**context) -> None:
    """
    파이프라인 완료 후 Slack에 성공 요약 알림 전송.
    실패 알림과 달리 성공 알림은 파이프라인을 중단시키지 않는다.
    """
    import asyncio

    from app.services.slack_notifier import notify_success

    run_date: str = context["ti"].xcom_pull(key="run_date", task_ids="fetch_matches")
    total_fetched: int = context["ti"].xcom_pull(key="total_fetched", task_ids="fetch_matches") or 0
    upserted: int = context["ti"].xcom_pull(key="upserted_count", task_ids="calculate_stats") or 0

    message = (
        f"TFT 일일 파이프라인 완료 ({run_date})\n"
        f"수집 매치: {total_fetched} | 업데이트 컴프: {upserted}"
    )
    try:
        asyncio.run(notify_success(message))
    except Exception as exc:
        # 알림 실패는 파이프라인 실패로 처리하지 않음
        logger.warning("[send_push_notification] Slack 알림 실패 (무시): %s", exc)


# ---------------------------------------------------------------------------
# DAG 정의
# ---------------------------------------------------------------------------

with DAG(
    dag_id="tft_daily_meta_update",
    default_args=DEFAULT_ARGS,
    description=(
        "매일 19:00 UTC KR/NA/EUW 마스터+ 매치 수집 → 컴프 클러스터링 → "
        "통계 계산 → AI 요약 → 캐시 갱신 → Slack 알림"
    ),
    schedule="0 19 * * *",      # 19:00 UTC = 04:00 KST
    start_date=datetime(2026, 3, 1),
    catchup=False,
    dagrun_timeout=timedelta(hours=3),
    tags=["tft", "meta", "pipeline"],
) as dag:

    sync_images = PythonOperator(
        task_id="sync_images",
        python_callable=task_sync_images,
    )

    fetch_matches = PythonOperator(
        task_id="fetch_matches",
        python_callable=task_fetch_matches,
    )

    parse_matches = PythonOperator(
        task_id="parse_matches",
        python_callable=task_parse_matches,
    )

    cluster_comps = PythonOperator(
        task_id="cluster_comps",
        python_callable=task_cluster_comps,
    )

    calculate_stats = PythonOperator(
        task_id="calculate_stats",
        python_callable=task_calculate_stats,
    )

    generate_ai_summary = PythonOperator(
        task_id="generate_ai_summary",
        python_callable=task_generate_ai_summary,
    )

    update_cache = PythonOperator(
        task_id="update_cache",
        python_callable=task_update_cache,
    )

    send_push_notification = PythonOperator(
        task_id="send_push_notification",
        python_callable=task_send_push_notification,
        trigger_rule="all_done",  # 이전 태스크 실패해도 알림은 항상 실행
    )

    # 의존성 체인
    (
        sync_images
        >> fetch_matches
        >> parse_matches
        >> cluster_comps
        >> calculate_stats
        >> generate_ai_summary
        >> update_cache
        >> send_push_notification
    )
