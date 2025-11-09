from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests

from config import get_settings


settings = get_settings()

logger = logging.getLogger(__name__)


def _headers() -> Dict[str, str]:
    return {
        "x-api-key": settings.ihub_api_key,
        "Content-Type": "application/json",
    }


def _build_url(path: str) -> str:
    base = settings.ihub_base_url
    return f"{base}{path if path.startswith('/') else '/' + path}"


def create_conversation(query: str) -> Dict[str, Any]:
    """Create a new conversation with the iHub Assistant."""
    if settings.use_mock_api:
        return _mock_create_conversation(query)

    url = _build_url("/assistant/conversations")
    logger.info("[STRAVITO_CLIENT] Creating conversation for query: %s...", query[:50])
    response = requests.post(url, headers=_headers(), json={"message": query}, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    logger.info(
        "[STRAVITO_CLIENT] Conversation created: ID=%s",
        response_data.get("conversationId")
        or response_data.get("conversation_id")
        or response_data.get("id"),
    )
    return response_data


def extract_sources(response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract and format source URLs from iHub response."""
    sources: List[Dict[str, str]] = []
    for src in response.get("sources", []) or []:
        title = src.get("title") or "View Source"
        url = src.get("url") or ""
        if url:
            sources.append(
                {
                    "title": title,
                    "url": url,
                    "description": src.get("description", ""),
                    "type": src.get("type", ""),
                    "published_at": src.get("published_at"),
                }
            )
    return sources


def get_message(
    conversation_id: str,
    message_id: str,
    max_retries: Optional[int] = None,
    retry_interval: Optional[float] = None,
) -> Dict[str, Any]:
    """Get a specific message from a conversation, polling until completion."""
    if settings.use_mock_api:
        return _mock_get_message(conversation_id, message_id)

    url = _build_url(
        f"/assistant/conversations/{conversation_id}/messages/{message_id}"
    )
    max_retries = max_retries or settings.stravito_poll_max_retries
    retry_interval = retry_interval or settings.stravito_poll_interval

    logger.info(
        "[STRAVITO_CLIENT] Fetching message: conversation=%s, message=%s",
        conversation_id,
        message_id,
    )

    retry_count = 0
    start_time = time.time()
    response_data: Optional[Dict[str, Any]] = None

    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=_headers(), timeout=30)
            response.raise_for_status()
            response_data = response.json()
            state = (response_data.get("state") or "").upper()

            logger.debug(
                "[STRAVITO_CLIENT] Poll #%s: State=%s",
                retry_count + 1,
                state or "UNKNOWN",
            )

            if state == "COMPLETED":
                elapsed = time.time() - start_time
                logger.info(
                    "[STRAVITO_CLIENT] ✅ Message completed in %.1fs after %s polls",
                    elapsed,
                    retry_count + 1,
                )
                sources = response_data.get("sources", [])
                logger.info(
                    "[STRAVITO_CLIENT]   - Message length: %s",
                    len(response_data.get("message", "") or ""),
                )
                logger.info(
                    "[STRAVITO_CLIENT]   - Sources found: %s", len(sources)
                )
                if sources:
                    for idx, source in enumerate(sources, start=1):
                        logger.info(
                            "[STRAVITO_CLIENT]     [%s] ID=%s Title=%s",
                            idx,
                            source.get("sourceId") or source.get("id"),
                            (source.get("title") or "N/A")[:50],
                        )
                else:
                    logger.warning(
                        "[STRAVITO_CLIENT]   - WARNING: No sources in completed response!"
                    )
                    logger.debug(
                        "[STRAVITO_CLIENT]   - Response keys: %s",
                        list(response_data.keys()),
                    )
                response_data["sources_extracted"] = extract_sources(response_data)
                return response_data

            if state in {"FAILED", "ERROR"}:
                logger.error(
                    "[STRAVITO_CLIENT] ❌ Message processing failed with state: %s",
                    state,
                )
                logger.error(
                    "[STRAVITO_CLIENT] Error message: %s",
                    response_data.get("error", "Unknown error"),
                )
                response_data["sources_extracted"] = extract_sources(response_data)
                return response_data

            if state in {"PROCESSING", "PENDING", "IN_PROGRESS", ""}:
                if retry_count == 0:
                    logger.info(
                        "[STRAVITO_CLIENT] ⏳ Message is processing, polling every %ss",
                        retry_interval,
                    )
                elif retry_count % 10 == 0:
                    elapsed = time.time() - start_time
                    logger.info(
                        "[STRAVITO_CLIENT] ⏳ Still waiting... (%.0fs elapsed)", elapsed
                    )
            else:
                logger.warning(
                    "[STRAVITO_CLIENT] ⚠️ Unknown state: %s; treating as in-progress",
                    state,
                )

            retry_count += 1
            time.sleep(retry_interval)
        except requests.exceptions.RequestException as exc:
            retry_count += 1
            logger.warning(
                "[STRAVITO_CLIENT] ⚠️ Request error on poll #%s: %s",
                retry_count,
                exc,
            )
            if retry_count >= max_retries:
                raise
            time.sleep(retry_interval)

    elapsed = time.time() - start_time
    logger.warning(
        "[STRAVITO_CLIENT] ⏱️ Timeout after %.1fs (%s polls)", elapsed, max_retries
    )
    if response_data is None:
        response_data = {"state": "TIMEOUT", "message": "", "sources": []}
    response_data["sources_extracted"] = extract_sources(response_data)
    return response_data


def send_followup(conversation_id: str, query: str) -> Dict[str, Any]:
    """Send a follow-up message to an existing conversation."""
    if settings.use_mock_api:
        return _mock_send_followup(conversation_id, query)

    url = _build_url(f"/assistant/conversations/{conversation_id}/messages")
    response = requests.post(
        url, headers=_headers(), json={"message": query}, timeout=30
    )
    response.raise_for_status()
    return response.json()


def give_feedback(message_id: str, feedback: str = "success") -> Dict[str, Any]:
    """Provide feedback on a message."""
    if settings.use_mock_api:
        return {"message_id": message_id, "feedback": feedback, "status": "mocked"}

    url = _build_url(f"/assistant/messages/{message_id}/feedback")
    response = requests.post(
        url, headers=_headers(), json={"feedback": feedback}, timeout=30
    )
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _mock_sources() -> List[Dict[str, Any]]:
    recent_date = (datetime.utcnow() - timedelta(days=180)).isoformat() + "Z"
    outdated_date = (datetime.utcnow() - timedelta(days=1500)).isoformat() + "Z"
    return [
        {
            "title": "Category Tracker Q2 2024",
            "url": "https://insights.example.com/category-tracker-q2-2024",
            "description": "Panel-based quantitative sales tracker for markers.",
            "type": "quantitative forecast",
            "published_at": recent_date,
        },
        {
            "title": "Brand POV: Sharpie vs Paper Mate",
            "url": "https://insights.example.com/brand-pov-sharpie-paper-mate",
            "description": "Contextual analysis of brand positioning within writing instruments.",
            "type": "brand presentation",
            "published_at": outdated_date,
        },
    ]


def _mock_message_payload(conversation_id: str, query: str) -> Dict[str, Any]:
    message_id = str(uuid4())
    sources = extract_sources({"sources": _mock_sources()})
    text = (
        "Here’s a mock insight for testing purposes.\n"
        f"- Focused question: {query}\n"
        "- Evidence comes from a recent quantitative tracker and a contextual brand POV.\n"
        "Treat this output as sample data only."
    )
    return {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "message": {
            "id": message_id,
            "text": text,
            "sources": sources,
            "sources_extracted": sources,
        },
    }


def _mock_create_conversation(query: str) -> Dict[str, Any]:
    conversation_id = str(uuid4())
    response = _mock_message_payload(conversation_id, query)
    response["conversation_id"] = conversation_id
    return response


def _mock_send_followup(conversation_id: str, query: str) -> Dict[str, Any]:
    return _mock_message_payload(conversation_id, query)


def _mock_get_message(conversation_id: str, message_id: str) -> Dict[str, Any]:
    sources = extract_sources({"sources": _mock_sources()})
    return {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "text": "Mock follow-up message.",
        "message": "Mock follow-up message.",
        "sources": sources,
        "sources_extracted": sources,
    }

