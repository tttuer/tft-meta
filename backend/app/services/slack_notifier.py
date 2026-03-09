"""
Slack 에러 알림 서비스.

파이프라인 태스크 실패 시 SLACK_WEBHOOK_URL로 알림 전송.
메시지 형식: "[TFT Pipeline] {task_name} 실패 - {error_message} ({timestamp})"

httpx 사용 (OpenAI SDK 미사용).
"""
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _now_kst() -> str:
    """현재 시각을 KST 문자열로 반환 (UTC+9)."""
    from datetime import timedelta
    kst = timezone(timedelta(hours=9))
    return datetime.now(tz=kst).strftime("%Y-%m-%d %H:%M:%S KST")


async def _send_webhook(payload: dict) -> None:
    """Slack Incoming Webhook으로 메시지 전송."""
    webhook_url = settings.slack_webhook_url
    if not webhook_url:
        logger.debug("[Slack] SLACK_WEBHOOK_URL 미설정. 알림 스킵.")
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json=payload)
        if resp.status_code != 200:
            logger.warning(
                "[Slack] 알림 전송 실패: status=%d body=%s",
                resp.status_code, resp.text[:200],
            )
        else:
            logger.debug("[Slack] 알림 전송 성공")


async def notify_failure(task_name: str, error_message: str) -> None:
    """
    파이프라인 태스크 실패 알림 전송.

    Args:
        task_name: 실패한 Airflow 태스크 이름
        error_message: 오류 메시지 (긴 경우 내부에서 잘라냄)
    """
    timestamp = _now_kst()
    short_error = error_message[:200] if len(error_message) > 200 else error_message
    text = f"[TFT Pipeline] {task_name} 실패 - {short_error} ({timestamp})"

    payload = {
        "text": text,
        "attachments": [
            {
                "color": "#FF0000",
                "fields": [
                    {"title": "태스크", "value": task_name, "short": True},
                    {"title": "시각", "value": timestamp, "short": True},
                    {"title": "오류", "value": short_error, "short": False},
                ],
            }
        ],
    }

    try:
        await _send_webhook(payload)
    except Exception as exc:
        # 알림 실패는 파이프라인을 중단시키지 않는다
        logger.warning("[Slack] notify_failure 전송 중 예외: %s", exc)


async def notify_success(message: str) -> None:
    """
    파이프라인 성공 알림 전송.

    Args:
        message: 성공 메시지 (자유 형식)
    """
    timestamp = _now_kst()
    payload = {
        "text": f"[TFT Pipeline] {message} ({timestamp})",
        "attachments": [
            {
                "color": "#36A64F",
                "fields": [
                    {"title": "시각", "value": timestamp, "short": True},
                ],
            }
        ],
    }

    try:
        await _send_webhook(payload)
    except Exception as exc:
        logger.warning("[Slack] notify_success 전송 중 예외: %s", exc)


async def notify_warning(task_name: str, message: str) -> None:
    """
    파이프라인 경고 알림 전송 (태스크는 계속 진행).

    Args:
        task_name: 경고가 발생한 태스크 이름
        message: 경고 메시지
    """
    timestamp = _now_kst()
    payload = {
        "text": f"[TFT Pipeline] {task_name} 경고 - {message} ({timestamp})",
        "attachments": [
            {
                "color": "#FFA500",
                "fields": [
                    {"title": "태스크", "value": task_name, "short": True},
                    {"title": "시각", "value": timestamp, "short": True},
                    {"title": "내용", "value": message, "short": False},
                ],
            }
        ],
    }

    try:
        await _send_webhook(payload)
    except Exception as exc:
        logger.warning("[Slack] notify_warning 전송 중 예외: %s", exc)
