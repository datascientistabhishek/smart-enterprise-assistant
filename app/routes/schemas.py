# app/routes/schemas.py
"""
Request and Response schemas.
Pydantic validates all inputs automatically — this is the guardrails layer.
"""

from pydantic import BaseModel, field_validator
from typing import Any


class AskRequest(BaseModel):
    question: str
    session_id: str = "default"

    @field_validator("question")
    @classmethod
    def question_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty.")
        if len(v) < 3:
            raise ValueError("Question is too short to be meaningful.")
        if len(v) > 1000:
            raise ValueError("Question exceeds 1000 characters. Please shorten it.")
        return v

    @field_validator("session_id")
    @classmethod
    def session_id_must_be_safe(cls, v: str) -> str:
        v = v.strip()
        if not v:
            return "default"
        if len(v) > 64:
            raise ValueError("session_id too long (max 64 chars).")
        return v


class ActionResult(BaseModel):
    success: bool
    message: str
    data: Any = None


class AskResponse(BaseModel):
    session_id: str
    answer: str
    action_result: ActionResult | None = None
    history_length: int
    error: str | None = None
