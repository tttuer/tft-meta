"""
AI 요약 서비스.

우선순위:
  1. GitHub Copilot API (GITHUB_TOKEN 설정 시) — gpt-4o-mini, 쿼터 차감 없음
  2. OpenRouter (OPENROUTER_API_KEY 설정 시) — 폴백

제공 기능:
  - generate_comp_summary: 컴프 단건 요약 (기존)
  - generate_meta_summary: 오늘의 메타 전체 요약 (기존)
  - generate_comp_strategy_summary: 컴프 전략 가이드 (STEP 2 신규, 150자 이내 한국어)
  - generate_meta_change_summary: 전날 대비 메타 변화 요약 (STEP 2 신규)
"""
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
COPILOT_CHAT_URL = "https://api.githubcopilot.com/chat/completions"

_copilot_token: str = ""
_copilot_token_expires_at: float = 0.0


async def _get_copilot_token() -> str:
    """ghu_ OAuth 토큰으로 Copilot 세션 토큰 발급 (30분마다 자동 갱신)."""
    global _copilot_token, _copilot_token_expires_at

    if _copilot_token and time.time() < _copilot_token_expires_at - 60:
        return _copilot_token

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            COPILOT_TOKEN_URL,
            headers={
                "Authorization": f"token {settings.github_token}",
                "Accept": "application/json",
                "Editor-Version": "vscode/1.85.1",
                "Editor-Plugin-Version": "copilot-chat/0.12.2",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    _copilot_token = data["token"]
    _copilot_token_expires_at = data.get("expires_at", time.time() + 1800)
    logger.debug("Copilot 세션 토큰 갱신 완료")
    return _copilot_token


async def _chat_copilot(messages: list[dict], max_tokens: int = 512) -> str:
    """GitHub Copilot Chat Completions API 호출."""
    token = await _get_copilot_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Editor-Version": "vscode/1.85.1",
        "Editor-Plugin-Version": "copilot-chat/0.12.2",
        "OpenAI-Intent": "conversation-panel",
    }
    payload = {
        "model": settings.github_copilot_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(COPILOT_CHAT_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


async def _chat_openrouter(messages: list[dict], max_tokens: int = 512) -> str:
    """OpenRouter Chat Completions API 호출."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tft-meta-advisor.local",
        "X-Title": "TFT Meta Advisor",
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


async def _chat(messages: list[dict], max_tokens: int = 512) -> str:
    """AI 호출 — GitHub Copilot 우선, 없으면 OpenRouter 폴백."""
    if settings.github_token:
        return await _chat_copilot(messages, max_tokens)
    if settings.openrouter_api_key:
        return await _chat_openrouter(messages, max_tokens)
    return "AI API 키가 설정되지 않았습니다. GITHUB_TOKEN 또는 OPENROUTER_API_KEY를 설정하세요."


# ---------------------------------------------------------------------------
# 기존 함수 (STEP 1 호환 유지)
# ---------------------------------------------------------------------------

async def generate_comp_summary(
    comp_name: str,
    win_rate: float,
    top4_rate: float,
    core_units: dict,
    traits: list[str],
) -> str:
    """컴프 단건 AI 전략 요약 생성 (STEP 1 기존 시그니처 유지)."""
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
    """오늘의 메타 전체 요약 생성 (STEP 1 기존 시그니처 유지)."""
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


# ---------------------------------------------------------------------------
# STEP 2 신규 함수
# ---------------------------------------------------------------------------

async def generate_comp_strategy_summary(
    name: str,
    win_rate: float,
    avg_placement: float,
    core_units: dict,
    traits: list[str],
) -> str:
    """
    컴프별 전략 요약 — 150자 이내 한국어.

    포함 항목:
      1. 핵심 강점 (1~2문장)
      2. 진입 조건 3가지 (각 1문장)
      3. 약점 또는 카운터 (1문장)
    """
    core_units_str = (
        ", ".join(core_units.get("8", core_units.get("7", [])))
        if core_units else "정보 없음"
    )
    traits_str = ", ".join(traits) if traits else "정보 없음"

    messages = [
        {
            "role": "system",
            "content": "당신은 TFT 전문 코치입니다. 한국어로 간결하고 실용적인 전략 가이드를 작성하세요.",
        },
        {
            "role": "user",
            "content": (
                "다음 TFT 컴프 데이터를 분석하여 전략 가이드를 작성하세요.\n"
                f"컴프명: {name} / 승률: {win_rate * 100:.1f}% / 평균 순위: {avg_placement:.2f}\n"
                f"코어 챔피언: {core_units_str} / 주요 시너지: {traits_str}\n\n"
                "포함 항목:\n"
                "1. 이 덱의 핵심 강점 (1~2문장)\n"
                "2. 진입 조건 3가지 (각 1문장)\n"
                "3. 주의할 약점 또는 카운터 (1문장)\n"
                "총 150자 이내"
            ),
        },
    ]

    try:
        return await _chat(messages, max_tokens=256)
    except Exception as exc:
        logger.warning("컴프 전략 요약 실패 (%s): %s", name, exc)
        return f"{name} — 전략 요약을 불러올 수 없습니다."


async def generate_meta_change_summary(
    current_comps: list[dict],
    patch_version: str,
    rising_comps: list[str] | None = None,
    falling_comps: list[str] | None = None,
    new_comps: list[str] | None = None,
) -> str:
    """
    오늘의 메타 변화 요약 (전날 대비 상위 5개 컴프 분석).
    3문장 한국어.

    Args:
        current_comps: 오늘 상위 컴프 list[{"name": str, "win_rate": float, "tier": str}]
        patch_version: 현재 패치 버전
        rising_comps: 전날 대비 승률 상승 컴프 이름 목록
        falling_comps: 전날 대비 승률 하락 컴프 이름 목록
        new_comps: 새로 등장한 컴프 이름 목록
    """
    rising = ", ".join(rising_comps) if rising_comps else "없음"
    falling = ", ".join(falling_comps) if falling_comps else "없음"
    new = ", ".join(new_comps) if new_comps else "없음"

    top5_lines = "\n".join(
        f"- {c['name']} (승률: {c['win_rate'] * 100:.1f}%, 티어: {c['tier']})"
        for c in current_comps[:5]
    )

    messages = [
        {
            "role": "system",
            "content": "당신은 TFT 메타 분석가입니다.",
        },
        {
            "role": "user",
            "content": (
                "다음 메타 변화 데이터를 분석하여 오늘의 메타 요약을 한국어 3문장으로 작성하세요.\n"
                f"패치: {patch_version}\n"
                f"상승 컴프: {rising} / 하락 컴프: {falling} / 신규 등장: {new}\n"
                f"오늘 상위 컴프:\n{top5_lines}"
            ),
        },
    ]

    try:
        return await _chat(messages, max_tokens=300)
    except Exception as exc:
        logger.warning("메타 변화 요약 실패: %s", exc)
        return "현재 메타 변화 데이터를 분석 중입니다."
