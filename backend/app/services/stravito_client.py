from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests

from config import get_settings


settings = get_settings()


def _headers() -> Dict[str, str]:
    return {
        "x-api-key": settings.ihub_api_key,
        "Content-Type": "application/json",
    }


def _build_url(path: str) -> str:
    base = settings.ihub_base_url
    return f"{base}{path if path.startswith('/') else '/' + path}"


def _log(msg: str) -> None:
    print(f"[STRAVITO_CLIENT] {msg}")


def create_conversation(query: str) -> Dict[str, Any]:
    """Create a new conversation with Stravito API or mock service."""
    if settings.use_mock_api:
        return _mock_create_conversation(query)

    url = _build_url("/assistant/conversations")
    _log(f"Creating conversation for query: {query[:50]}...")
    response = requests.post(url, headers=_headers(), json={"message": query}, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    _log(f"Conversation created: ID={response_data.get('conversationId') or response_data.get('conversation_id')}")
    if isinstance(response_data, dict):
        response_data["sources_extracted"] = extract_sources(response_data)
    return response_data


def extract_sources(response: Dict[str, Any]) -> List[Dict[str, str]]:
    sources: List[Dict[str, str]] = []
    for src in response.get("sources", []) or []:
        title = src.get("title") or "View Source"
        url = src.get("url") or ""
        if not url:
            continue
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
    """Get a specific message from a conversation, polling until status is COMPLETED."""
    if settings.use_mock_api:
        return _mock_get_message(conversation_id, message_id)

    max_retries = max_retries or settings.stravito_poll_max_retries
    retry_interval = retry_interval or settings.stravito_poll_interval

    url = _build_url(f"/assistant/conversations/{conversation_id}/messages/{message_id}")
    _log(f"Fetching message: conversation={conversation_id}, message={message_id}")

    retry_count = 0
    start_time = time.time()
    response_data: Optional[Dict[str, Any]] = None

    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=_headers(), timeout=30)
            response.raise_for_status()
            response_data = response.json()
            state = (response_data.get("state") or "").upper()

            _log(f"Poll #{retry_count + 1}: State = {state or 'UNKNOWN'}")

            if state == "COMPLETED":
                elapsed = time.time() - start_time
                _log(f"✅ Message completed in {elapsed:.1f}s after {retry_count + 1} polls")
                sources = response_data.get("sources", [])
                message_content = response_data.get("message", "")
                _log("Message retrieved:")
                _log(f"  - Message length: {len(message_content or '')}")
                _log(f"  - Sources found: {len(sources)}")
                if sources:
                    _log("  - Source details:")
                    for idx, source in enumerate(sources, start=1):
                        _log(
                            f"    [{idx}] ID: {source.get('sourceId', 'N/A')}, "
                            f"Title: {(source.get('title') or 'N/A')[:50]}"
                        )
                else:
                    _log("  - WARNING: No sources in completed response!")
                    _log(f"  - Response keys: {list(response_data.keys())}")

                response_data["sources_extracted"] = extract_sources(response_data)
                return response_data

            if state in {"FAILED", "ERROR"}:
                _log(f"❌ Message processing failed with state: {state}")
                _log(f"Error message: {response_data.get('error', 'Unknown error')}")
                response_data["sources_extracted"] = extract_sources(response_data)
                return response_data

            # in-progress states
            if retry_count == 0:
                _log(f"⏳ Message is processing, will poll every {retry_interval}s...")
            elif retry_count % 10 == 0:
                elapsed = time.time() - start_time
                _log(f"⏳ Still waiting... ({elapsed:.0f}s elapsed)")

            retry_count += 1
            time.sleep(retry_interval)

        except requests.exceptions.RequestException as exc:
            retry_count += 1
            _log(f"⚠️  Request error on poll #{retry_count}: {exc}")
            if retry_count >= max_retries:
                raise
            time.sleep(retry_interval)

    elapsed = time.time() - start_time
    _log(f"⏱️  Timeout after {elapsed:.1f}s ({max_retries} polls)")
    _log("⚠️  Message did not complete, returning last response")

    if response_data is None:
        response_data = {"state": "TIMEOUT", "message": "", "sources": []}
    response_data["sources_extracted"] = extract_sources(response_data)
    return response_data


def send_followup(conversation_id: str, query: str) -> Dict[str, Any]:
    """Send a follow-up message to an existing conversation."""
    if settings.use_mock_api:
        return _mock_send_followup(conversation_id, query)

    url = _build_url(f"/assistant/conversations/{conversation_id}/messages")
    response = requests.post(url, headers=_headers(), json={"message": query}, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    if isinstance(response_data, dict):
        response_data["sources_extracted"] = extract_sources(response_data)
    return response_data


def give_feedback(message_id: str, feedback: str = "success") -> Dict[str, Any]:
    """Provide feedback on a message."""
    if settings.use_mock_api:
        return {"message_id": message_id, "feedback": feedback, "status": "mocked"}

    url = _build_url(f"/assistant/messages/{message_id}/feedback")
    response = requests.post(url, headers=_headers(), json={"feedback": feedback}, timeout=30)
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
        "conversationId": conversation_id,
        "message_id": message_id,
        "messageId": message_id,
        "message": {
            "id": message_id,
            "text": text,
            "sources": sources,
            "sources_extracted": sources,
            "state": "COMPLETED",
        },
        "state": "COMPLETED",
        "sources": sources,
        "sources_extracted": sources,
    }


def _mock_create_conversation(query: str) -> Dict[str, Any]:
    conversation_id = str(uuid4())
    response = _mock_message_payload(conversation_id, query)
    _log(f"[MOCK] Conversation created: ID={conversation_id}")
    return response


def _mock_send_followup(conversation_id: str, query: str) -> Dict[str, Any]:
    _log(f"[MOCK] Sending follow-up to conversation={conversation_id}")
    return _mock_message_payload(conversation_id, query)


def _mock_get_message(conversation_id: str, message_id: str) -> Dict[str, Any]:
    _log(f"[MOCK] Fetching message message_id={message_id}")
    payload = _mock_message_payload(conversation_id, "mock follow up")
    payload["message_id"] = message_id
    payload["messageId"] = message_id
    return payload