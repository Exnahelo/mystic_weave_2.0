from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from api.companions import Companion, CreatureCompanion, ExceptionalCompanion, SapientCompanion


class CreateCompanionRequest(BaseModel):
    session_id: str
    handler_id: str
    tier: Literal["sapient", "creature", "exceptional"]
    companion: Companion

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_companion_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        companion = data.get("companion")
        tier = data.get("tier")
        if not isinstance(companion, dict):
            return data

        normalized = dict(companion)
        if tier is not None and "tier" not in normalized:
            normalized["tier"] = tier
        if "subspecies" not in normalized and "subtype" in normalized:
            normalized["subspecies"] = normalized["subtype"]

        return {**data, "companion": normalized}

    @model_validator(mode="after")
    def validate_tier_matches_companion(self) -> "CreateCompanionRequest":
        tier_map = {
            "sapient": SapientCompanion,
            "creature": CreatureCompanion,
            "exceptional": ExceptionalCompanion,
        }
        expected_type = tier_map[self.tier]
        if not isinstance(self.companion, expected_type):
            raise ValueError(f"tier={self.tier!r} does not match companion payload")
        return self


class TransitionCompanionRequest(BaseModel):
    session_id: str
    new_companion: ExceptionalCompanion
    trigger: str

    model_config = ConfigDict(extra="forbid")


class CompanionResponse(BaseModel):
    companion_id: str
    companion: Companion
    archived: bool = False

    model_config = ConfigDict(extra="forbid")