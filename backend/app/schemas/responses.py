import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


# --- Champion ---
class ChampionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    cost: int
    traits: list
    best_items: dict
    item_reasoning: dict
    image_url: str | None
    splash_url: str | None = None


# --- Augment ---
class AugmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    tier: str
    description: str | None
    image_url: str | None
    comp_synergy: list


# --- Comp ---
class CompSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    tier: str
    win_rate: float
    top4_rate: float
    avg_placement: float
    play_rate: float
    sample_count: int
    patch_version: str
    updated_at: datetime
    core_units: dict  # {"6": [...], "7": [...], "8": [...], "9": [...]}

    @computed_field
    @property
    def preview_champions(self) -> list[str]:
        """최고 레벨의 챔피언 ID 목록 — 카드 UI 미리보기용."""
        if not self.core_units:
            return []
        level_keys = [k for k in self.core_units if str(k).isdigit()]
        if not level_keys:
            return []
        highest = str(max(int(k) for k in level_keys))
        champs = self.core_units.get(highest, [])
        return [str(c) for c in champs] if isinstance(champs, list) else []


class CompDetailSchema(CompSummarySchema):
    core_units: dict
    board_positions: list
    recommended_augments: dict
    entry_conditions: list
    ai_summary: str | None


class BoardSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comp_id: uuid.UUID
    comp_name: str
    board_positions: list


# --- Meta Summary ---
class MetaSummarySchema(BaseModel):
    patch_version: str
    generated_at: str
    top_comps: list[CompSummarySchema]
    ai_summary: str


# --- Health ---
class HealthSchema(BaseModel):
    status: str
    db_connected: bool
    version: str = "0.1.0"
