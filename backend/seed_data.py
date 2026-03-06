"""
Seed script: inserts 3 dummy comps for local development testing.
Run: uv run python seed_data.py
"""
import asyncio
import uuid
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models.comp import Comp


DUMMY_COMPS = [
    {
        "id": uuid.uuid4(),
        "name": "이렐리아 전사",
        "tier": "S",
        "win_rate": 0.22,
        "top4_rate": 0.58,
        "avg_placement": 3.1,
        "play_rate": 0.12,
        "sample_count": 1500,
        "core_units": {
            "6": ["Irelia", "Garen", "Darius"],
            "7": ["Irelia", "Garen", "Darius", "Camille"],
            "8": ["Irelia", "Garen", "Darius", "Camille", "Xin Zhao"],
        },
        "board_positions": [
            {"row": 3, "col": 0, "champion_id": "Garen", "items": []},
            {"row": 3, "col": 2, "champion_id": "Darius", "items": ["Warmog's Armor"]},
            {"row": 3, "col": 4, "champion_id": "Irelia", "items": ["Blade of the Ruined King", "Rabadon's Deathcap"]},
        ],
        "recommended_augments": {
            "2-1": ["Duelist Heart", "Warrior Crest"],
            "3-2": ["Blade Waltz"],
            "4-2": ["Irelia Emblem"],
        },
        "entry_conditions": ["3코스트 유닛 3성 보유", "전사 4 이상 활성화"],
        "ai_summary": "이렐리아를 중심으로 전사 시너지를 극대화하는 컴프입니다. 초반 전사 코어를 빠르게 완성하고 후반 이렐리아에 BIS 아이템을 집중하세요.",
        "patch_version": "14.x",
        "updated_at": datetime.utcnow(),
    },
    {
        "id": uuid.uuid4(),
        "name": "럭스 마법사",
        "tier": "A",
        "win_rate": 0.18,
        "top4_rate": 0.52,
        "avg_placement": 3.5,
        "play_rate": 0.09,
        "sample_count": 1100,
        "core_units": {
            "6": ["Lux", "Syndra", "Orianna"],
            "7": ["Lux", "Syndra", "Orianna", "Veigar"],
            "8": ["Lux", "Syndra", "Orianna", "Veigar", "Karma"],
        },
        "board_positions": [
            {"row": 3, "col": 1, "champion_id": "Syndra", "items": []},
            {"row": 3, "col": 3, "champion_id": "Orianna", "items": ["Chalice of Power"]},
            {"row": 3, "col": 5, "champion_id": "Lux", "items": ["Jeweled Gauntlet", "Rabadon's Deathcap"]},
        ],
        "recommended_augments": {
            "2-1": ["Sorcerer Heart"],
            "3-2": ["Lux Emblem"],
            "4-2": ["Blue Battery"],
        },
        "entry_conditions": ["마법사 4 이상 활성화", "럭스 2성 이상"],
        "ai_summary": "럭스의 강력한 광역 스킬을 중심으로 마법사 시너지로 AP를 극대화하는 컴프입니다.",
        "patch_version": "14.x",
        "updated_at": datetime.utcnow(),
    },
    {
        "id": uuid.uuid4(),
        "name": "카이사 사수",
        "tier": "A",
        "win_rate": 0.17,
        "top4_rate": 0.50,
        "avg_placement": 3.7,
        "play_rate": 0.08,
        "sample_count": 950,
        "core_units": {
            "6": ["Kai'Sa", "Jinx", "Ashe"],
            "7": ["Kai'Sa", "Jinx", "Ashe", "Ezreal"],
            "8": ["Kai'Sa", "Jinx", "Ashe", "Ezreal", "Sivir"],
        },
        "board_positions": [
            {"row": 3, "col": 0, "champion_id": "Jinx", "items": []},
            {"row": 3, "col": 2, "champion_id": "Ashe", "items": ["Giant Slayer"]},
            {"row": 3, "col": 6, "champion_id": "Kai'Sa", "items": ["Guinsoo's Rageblade", "Runaan's Hurricane"]},
        ],
        "recommended_augments": {
            "2-1": ["Sniper Heart"],
            "3-2": ["Kai'Sa Emblem"],
            "4-2": ["Cybernetic Leech"],
        },
        "entry_conditions": ["사수 4 이상 활성화", "카이사 2성 이상"],
        "ai_summary": "카이사의 스택 기반 딜을 활용한 사수 컴프. 후반 카이사에게 어택스피드 아이템을 집중하세요.",
        "patch_version": "14.x",
        "updated_at": datetime.utcnow(),
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        for data in DUMMY_COMPS:
            comp = Comp(**data)
            session.add(comp)
        await session.commit()
    print(f"Seeded {len(DUMMY_COMPS)} comps successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
