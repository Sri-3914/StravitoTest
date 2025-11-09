from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ChatRequest, ChatResponse
from app.utils.guardrails import assess_guardrails, ensure_prompt_complete
from app.services import stravito_client


app = FastAPI(
    title="Stravito Guarded Chat",
    version="0.1.0",
    description="FastAPI backend for a guardrail-enabled Stravito chat assistant.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    prompt_status = ensure_prompt_complete(request)
    if not prompt_status.is_complete:
        message = (
            "I need a bit more context before I can help."
            if prompt_status.missing_fields
            else "Please clarify your request."
        )
        return ChatResponse(
            message=message,
            follow_up_needed=True,
            follow_up_prompt=prompt_status.follow_up_question,
        )

    try:
        if request.conversation_id:
            api_response = stravito_client.send_followup(
                request.conversation_id, request.message
            )
            conversation_id = request.conversation_id
        else:
            api_response = stravito_client.create_conversation(request.message)
            conversation_id = (
                api_response.get("conversation_id")
                or api_response.get("id")
                or api_response.get("conversation", {}).get("id")
            )
            if not conversation_id:
                raise ValueError("conversation_id missing from API response")

        message_payload = api_response.get("message") or api_response
        message_text = message_payload.get("text") or message_payload.get("message")
        message_id = (
            message_payload.get("message_id")
            or message_payload.get("id")
            or api_response.get("message_id")
        )

        if not message_text:
            # Fallback: fetch the most recent message if not returned inline
            if conversation_id and message_id:
                latest = stravito_client.get_message(conversation_id, message_id)
                message_text = latest.get("text") or latest.get("message", "")
                message_payload = latest
            else:
                message_text = "No response text returned from iHub."

        sources = message_payload.get("sources_extracted") or message_payload.get(
            "sources", []
        )

        guardrails = assess_guardrails(request, sources)

        if guardrails.fabrication_warning:
            message_text = (
                f"{guardrails.fabrication_warning}\n\n"
                f"I can outline a general approach:\n{message_text}"
            )

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            message=message_text,
            guardrails=guardrails,
            raw_sources=guardrails.source_flags,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Malformed response from iHub assistant: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with iHub assistant: {exc}",
        ) from exc

