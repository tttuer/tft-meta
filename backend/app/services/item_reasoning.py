"""
챔피언 아이템 추천 이유 생성 서비스.

"{champion_name}에게 {item_name}이 왜 좋은지 20자 이내 한국어로 설명"

OpenRouter + httpx 사용 (OpenAI SDK 미사용).
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def _chat(messages: list[dict]) -> str:
    """OpenRouter Chat Completions API 직접 호출."""
    if not settings.openrouter_api_key:
        return "OpenRouter API 키가 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tft-meta-advisor.local",
        "X-Title": "TFT Meta Advisor",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "max_tokens": 64,
        "temperature": 0.5,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"].strip()


async def explain_item_for_champion(
    champion_name: str,
    item_name: str,
) -> str:
    """
    특정 챔피언에게 특정 아이템이 좋은 이유를 20자 이내 한국어로 반환.

    Args:
        champion_name: 챔피언 이름 (예: "야스오")
        item_name: 아이템 이름 (예: "무한의 대검")

    Returns:
        20자 이내 한국어 설명 (예: "공격속도와 AP 모두 시너지")
    """
    messages = [
        {
            "role": "user",
            "content": (
                f"{champion_name}에게 {item_name}이 왜 좋은지 20자 이내 한국어로 설명하세요.\n"
                "예시: '공격속도와 AP 모두 시너지'\n"
                "반드시 20자 이내로, 이유만 간결하게 작성하세요."
            ),
        }
    ]

    try:
        result = await _chat(messages)
        # 20자 초과 시 잘라내기
        return result[:20] if len(result) > 20 else result
    except Exception as exc:
        logger.warning(
            "아이템 추천 이유 생성 실패 (%s + %s): %s",
            champion_name, item_name, exc,
        )
        return "시너지 효과 있음"


async def batch_explain_items(
    champion_name: str,
    item_names: list[str],
) -> dict[str, str]:
    """
    챔피언의 여러 아이템에 대한 추천 이유를 일괄 생성.

    Args:
        champion_name: 챔피언 이름
        item_names: 아이템 이름 목록

    Returns:
        {item_name: explanation} 딕셔너리
    """
    import asyncio

    results = await asyncio.gather(
        *[explain_item_for_champion(champion_name, item) for item in item_names],
        return_exceptions=True,
    )

    output: dict[str, str] = {}
    for item_name, result in zip(item_names, results):
        if isinstance(result, Exception):
            logger.warning("배치 아이템 설명 실패 (%s): %s", item_name, result)
            output[item_name] = "시너지 효과 있음"
        else:
            output[item_name] = result

    return output
