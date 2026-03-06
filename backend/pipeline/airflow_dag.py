"""
Airflow DAG: TFT 매치 데이터 수집 및 메타 분석
- 매일 오전 4시 실행
- fetch_matches → analyze_comps 순서
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "tft-meta-advisor",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def _fetch():
    import asyncio
    from pipeline.fetch_matches import run
    asyncio.run(run())


def _analyze():
    import asyncio
    from pipeline.analyze_comps import run
    asyncio.run(run())


with DAG(
    dag_id="tft_meta_pipeline",
    default_args=default_args,
    description="Daily TFT match ingestion and meta analysis",
    schedule="0 4 * * *",
    start_date=datetime(2026, 3, 1),
    catchup=False,
    tags=["tft", "meta"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_matches",
        python_callable=_fetch,
    )

    analyze_task = PythonOperator(
        task_id="analyze_comps",
        python_callable=_analyze,
    )

    fetch_task >> analyze_task
