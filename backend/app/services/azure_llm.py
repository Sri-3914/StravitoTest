from __future__ import annotations

from typing import Iterable, Optional

from openai import AzureOpenAI

from app.schemas import GuardrailAssessment, GuardrailSourceFlag
from config import get_settings


settings = get_settings()

client: Optional[AzureOpenAI] = None

if settings.enable_azure_llm:
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )


SYSTEM_PROMPT = (
    "You are the Stravito Guarded Assistant. Your task is to produce a final, "
    "truthful, and guarded response for business insights. Always respect the guardrail "
    "annotations provided. If evidence confidence is limited or no direct evidence "
    "exists, you must clearly state the limitation and avoid inventing facts. "
    "Only rely on the supplied sources. If a source is flagged as outdated, you must warn "
    "the user. Provide clear, structured answers with actionable guidance when possible."
)


def format_sources(sources: Iterable[GuardrailSourceFlag]) -> str:
    lines = []
    for idx, source in enumerate(sources, start=1):
        parts = [
            f"{idx}. Title: {source.title}",
            f"   URL: {source.url}",
            f"   Classification: {source.label}",
        ]
        if source.description:
            parts.append(f"   Summary: {source.description}")
        if source.published_at:
            age_note = (
                f" (approx. age: {source.age_in_years} years)" if source.age_in_years else ""
            )
            parts.append(f"   Published at: {source.published_at}{age_note}")
        if source.is_outdated:
            parts.append("   WARNING: Source older than 3 years.")
        lines.append("\n".join(parts))
    return "\n".join(lines) if lines else "No sources were returned."


def craft_guardrail_brief(assessment: GuardrailAssessment) -> str:
    lines = [
        f"Evidence confidence: {assessment.evidence_confidence}",
        f"Evidence summary: {assessment.evidence_summary}",
        f"Market scope: {assessment.market_scope}",
        f"Category scope: {assessment.category_scope}",
        f"Timeframe scope: {assessment.timeframe_scope}",
        f"Tiered market focus: {assessment.tiered_market_focus}",
    ]
    if assessment.fabrication_warning:
        lines.append(f"Fabrication warning: {assessment.fabrication_warning}")
    return "\n".join(lines)


def synthesize_final_answer(
    user_prompt: str,
    stravito_answer: str,
    assessment: GuardrailAssessment,
    sources: Iterable[GuardrailSourceFlag],
) -> Optional[str]:
    """Send conversation context to Azure OpenAI and return the synthesised message."""
    if not settings.enable_azure_llm or client is None:
        return None

    guardrail_brief = craft_guardrail_brief(assessment)
    sources_text = format_sources(sources)

    user_content = (
        "Original user prompt:\n"
        f"{user_prompt}\n\n"
        "Initial response from Stravito assistant:\n"
        f"{stravito_answer}\n\n"
        "Guardrail assessment:\n"
        f"{guardrail_brief}\n\n"
        "Source catalogue:\n"
        f"{sources_text}\n\n"
        "Instructions:\n"
        "- Produce a final answer that adheres to the guardrail assessment.\n"
        "- Clearly indicate where evidence is limited or outdated.\n"
        "- Do not fabricate data. If information is missing, state the gap and optionally "
        "outline a framework or next steps.\n"
        "- Reference sources inline using [#] notation matching the numbered list when relevant.\n"
    )

    completion = client.responses.create(
        model=settings.azure_openai_deployment,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
    )

    if not completion.output:
        return None

    first_choice = completion.output[0]
    if not first_choice.content:
        return None

    message = first_choice.content[0].text
    return message.strip() if isinstance(message, str) else None

