import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
