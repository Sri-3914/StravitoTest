from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

import requests

from config import get_settings


settings = get_settings()

HEADERS = (
    {
        "x-api-key": settings.ihub_api_key,
        "Content-Type": "application/json",
    }
    if not settings.use_mock_api
    else {}
)


def _build_url(path: str) -> str:
    base = settings.ihub_base_url
    return f"{base}{path if path.startswith('/') else '/' + path}"


def create_conversation(query: str) -> Dict[str, Any]:
    """Create a new conversation with the iHub Assistant."""
    if settings.use_mock_api:
        return _mock_create_conversation(query)

    url = _build_url("/assistant/conversations")
    response = requests.post(url, headers=HEADERS, json={"message": query}, timeout=30)
    response.raise_for_status()
    return response.json()


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


def get_message(conversation_id: str, message_id: str) -> Dict[str, Any]:
    """Get a specific message from a conversation."""
    if settings.use_mock_api:
        return _mock_get_message(conversation_id, message_id)

    url = _build_url(
        f"/assistant/conversations/{conversation_id}/messages/{message_id}"
    )
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    data["sources_extracted"] = extract_sources(data)
    return data


def send_followup(conversation_id: str, query: str) -> Dict[str, Any]:
    """Send a follow-up message to an existing conversation."""
    if settings.use_mock_api:
        return _mock_send_followup(conversation_id, query)

    url = _build_url(f"/assistant/conversations/{conversation_id}/messages")
    response = requests.post(
        url, headers=HEADERS, json={"message": query}, timeout=30
    )
    response.raise_for_status()
    return response.json()


def give_feedback(message_id: str, feedback: str = "success") -> Dict[str, Any]:
    """Provide feedback on a message."""
    if settings.use_mock_api:
        return {"message_id": message_id, "feedback": feedback, "status": "mocked"}

    url = _build_url(f"/assistant/messages/{message_id}/feedback")
    response = requests.post(
        url, headers=HEADERS, json={"feedback": feedback}, timeout=30
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

