from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from app.schemas import (
    ChatRequest,
    GuardrailAssessment,
    GuardrailPromptStatus,
    GuardrailSourceFlag,
    compute_age_in_years,
)

CRITICAL_PROMPT_FIELDS = ["market", "category", "timeframe"]

EMPIRICAL_KEYWORDS = ("forecast", "quant", "quantitative", "survey", "panel", "sales")
CONTEXTUAL_KEYWORDS = ("pov", "presentation", "overview", "brand", "strategy")

PRIORITY_MARKETS = ("united states", "mexico", "brazil")


def ensure_prompt_complete(request: ChatRequest) -> GuardrailPromptStatus:
    """Validate that the user prompt includes all required context dimensions."""
    missing = [
        field for field in CRITICAL_PROMPT_FIELDS if not getattr(request, field)
    ]
    if not missing:
        return GuardrailPromptStatus(is_complete=True)

    follow_up_parts = [
        "Could you provide the following details so I can give an accurate answer?"
    ]
    for field in missing:
        if field == "market":
            follow_up_parts.append(
                "- Which market should I focus on (e.g., United States, Mexico)?"
            )
        elif field == "category":
            follow_up_parts.append(
                "- Which product category is most relevant (e.g., pens, markers)?"
            )
        elif field == "timeframe":
            follow_up_parts.append(
                "- What timeframe should I consider (e.g., 2023 results, next 12 months)?"
            )

    follow_up_question = "\n".join(follow_up_parts)
    return GuardrailPromptStatus(
        is_complete=False, missing_fields=missing, follow_up_question=follow_up_question
    )


def _label_source_type(source: Dict[str, str]) -> str:
    title = (source.get("title") or "").lower()
    description = (source.get("description") or "").lower()
    source_type = (source.get("type") or "").lower()

    text_blob = " ".join([title, description, source_type])
    if any(keyword in text_blob for keyword in EMPIRICAL_KEYWORDS):
        return "empirical evidence"
    if any(keyword in text_blob for keyword in CONTEXTUAL_KEYWORDS):
        return "contextual reference"
    return "unspecified evidence"


def _transform_sources(
    sources: Iterable[Dict[str, str]]
) -> List[GuardrailSourceFlag]:
    flags: List[GuardrailSourceFlag] = []
    for src in sources:
        age_years = compute_age_in_years(src.get("published_at"))
        is_outdated = bool(age_years and age_years > 3)
        label = _label_source_type(src)
        flags.append(
            GuardrailSourceFlag(
                title=src.get("title", "View Source"),
                url=src.get("url", ""),
                type=src.get("type", ""),
                description=src.get("description", ""),
                published_at=src.get("published_at"),
                age_in_years=age_years,
                is_outdated=is_outdated,
                label=label,
            )
        )
    return flags


def _compute_evidence_confidence(
    sources: List[GuardrailSourceFlag],
) -> tuple[str, str, Optional[str]]:
    empirical_sources = [src for src in sources if src.label == "empirical evidence"]
    outdated_sources = [src for src in sources if src.is_outdated]
    if not sources:
        return (
            "no direct evidence",
            "No supporting sources were returned. I can outline a typical approach but do not have data-backed findings.",
            "I don’t have enough evidence to answer directly. I can share a general framework if helpful.",
        )
    if len(empirical_sources) >= 2 and not outdated_sources:
        return (
            "strong data",
            "Multiple recent empirical sources support these findings.",
            None,
        )
    if outdated_sources:
        return (
            "limited data",
            "Some sources may be outdated (>3 years old). Treat insights as directional only.",
            None,
        )
    return (
        "limited data",
        "Only a single or contextual source was identified. Consider validating with additional research.",
        None,
    )


def _tiered_market_summary(request: ChatRequest) -> str:
    if not request.market:
        return "Market emphasis pending; awaiting clarification."

    market_lower = request.market.lower()
    if market_lower in PRIORITY_MARKETS:
        return (
            f"Prioritized {request.market} due to strategic focus. Secondary markets were"
            " referenced only when directly relevant."
        )

    prioritized = ", ".join(m.title() for m in PRIORITY_MARKETS)
    return (
        f"Primary focus on {request.market}. Higher-weight markets ({prioritized})"
        " were deprioritized unless supporting data was available."
    )


def assess_guardrails(
    request: ChatRequest, raw_sources: Iterable[Dict[str, str]]
) -> GuardrailAssessment:
    """Run guardrail checks on the response from iHub."""
    source_flags = _transform_sources(raw_sources)
    evidence_confidence, evidence_summary, fabrication_warning = (
        _compute_evidence_confidence(source_flags)
    )

    market_scope = request.market or "Market unspecified"
    category_scope = request.category or "Category unspecified"
    timeframe_scope = request.timeframe or "Timeframe unspecified"

    return GuardrailAssessment(
        evidence_confidence=evidence_confidence,
        evidence_summary=evidence_summary,
        market_scope=f"In-market focus: {market_scope}",
        category_scope=f"Category focus: {category_scope}",
        timeframe_scope=f"Timeframe focus: {timeframe_scope}",
        tiered_market_focus=_tiered_market_summary(request),
        fabrication_warning=fabrication_warning,
        source_flags=source_flags,
    )

