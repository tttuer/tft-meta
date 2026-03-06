"""
OpenRouter AI 요약 서비스.
model: meta-llama/llama-3.3-70b-instruct:free
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def _chat(messages: list[dict]) -> str:
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
        "max_tokens": 512,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"].strip()


async def generate_comp_summary(comp_name: str, win_rate: float, top4_rate: float,
                                 core_units: dict, traits: list[str]) -> str:
    """컴프 단건 AI 전략 요약 생성."""
    traits_str = ", ".join(traits) if traits else "정보 없음"
    units_str = str(core_units.get("8") or core_units.get("7") or list(core_units.values())[:1])

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 TFT(Teamfight Tactics) 전문 코치입니다. "
                "주어진 컴프 정보를 바탕으로 한국어로 간결하고 실용적인 전략 요약을 작성하세요. "
                "3~5문장 이내로 작성하세요."
            ),
        },
        {
            "role": "user",
            "content": (
                f"컴프 이름: {comp_name}\n"
                f"승률: {win_rate:.1%}, 탑4율: {top4_rate:.1%}\n"
                f"코어 유닛: {units_str}\n"
                f"시너지: {traits_str}\n\n"
                "이 컴프의 핵심 전략과 운영 팁을 요약해주세요."
            ),
        },
    ]

    try:
        return await _chat(messages)
    except Exception as e:
        logger.warning("AI 요약 생성 실패 (%s): %s", comp_name, e)
        return f"{comp_name} 컴프 — AI 요약 생성 중 오류가 발생했습니다."


async def generate_meta_summary(top_comps: list[dict], patch_version: str) -> str:
    """오늘의 메타 전체 요약 생성."""
    comp_lines = "\n".join(
        f"- {c['name']} (티어: {c['tier']}, 승률: {c['win_rate']:.1%})"
        for c in top_comps[:5]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 TFT 메타 분석 전문가입니다. "
                "현재 패치의 메타 동향을 한국어로 3~5문장으로 요약하세요."
            ),
        },
        {
            "role": "user",
            "content": (
                f"패치 버전: {patch_version}\n"
                f"상위 컴프 목록:\n{comp_lines}\n\n"
                "현재 메타 동향과 플레이어에게 추천하는 전략을 요약해주세요."
            ),
        },
    ]

    try:
        return await _chat(messages)
    except Exception as e:
        logger.warning("메타 요약 생성 실패: %s", e)
        return "현재 메타 분석 데이터를 수집 중입니다."
