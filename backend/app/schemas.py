from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request payload from the frontend."""

    message: str = Field(..., description="User message or prompt")
    market: Optional[str] = Field(
        None, description="Primary market context (e.g., United States, Brazil)"
    )
    category: Optional[str] = Field(
        None, description="Product category context (e.g., pens, markers)"
    )
    timeframe: Optional[str] = Field(
        None, description="Relevant timeframe (e.g., 2023, 'next 12 months')"
    )
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation identifier"
    )


class GuardrailPromptStatus(BaseModel):
    """Result of prompt completeness guardrail."""

    is_complete: bool
    missing_fields: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None


class GuardrailSourceFlag(BaseModel):
    """Details about a single source."""

    title: str
    url: str
    type: str
    description: str
    published_at: Optional[str]
    is_outdated: bool = False
    age_in_years: Optional[float] = None
    label: str = Field(
        "...",
        description="Evidence vs. context label; e.g., 'empirical evidence', 'contextual reference'",
    )


class GuardrailAssessment(BaseModel):
    """Aggregate guardrail findings for a message."""

    evidence_confidence: str
    evidence_summary: str
    market_scope: str
    category_scope: str
    timeframe_scope: str
    tiered_market_focus: str
    fabrication_warning: Optional[str] = None
    source_flags: List[GuardrailSourceFlag] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Unified response model returned to the frontend."""

    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    message: str
    guardrails: Optional[GuardrailAssessment] = None
    raw_sources: List[GuardrailSourceFlag] = Field(default_factory=list)
    follow_up_needed: bool = False
    follow_up_prompt: Optional[str] = None


def compute_age_in_years(published_at: Optional[str]) -> Optional[float]:
    """Helper to compute age from ISO formatted date strings."""
    if not published_at:
        return None
    try:
        published_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    delta = datetime.utcnow() - published_date.replace(tzinfo=None)
    return round(delta.days / 365.25, 2)

