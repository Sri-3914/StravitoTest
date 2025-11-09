from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ChatRequest, ChatResponse
from app.utils.guardrails import assess_guardrails, ensure_prompt_complete
from app.services import stravito_client
from app.services.azure_llm import synthesize_final_answer


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
    def _extract_text(payload: object) -> str:
        if isinstance(payload, dict):
            text_candidate = payload.get("text")
            if isinstance(text_candidate, str) and text_candidate.strip():
                return text_candidate
            message_candidate = payload.get("message") or payload.get("content")
            if isinstance(message_candidate, dict):
                return (
                    message_candidate.get("text")
                    or message_candidate.get("content")
                    or ""
                )
            if isinstance(message_candidate, str):
                return message_candidate
            return ""
        if isinstance(payload, str):
            return payload
        return ""

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
                or api_response.get("conversationId")
                or api_response.get("id")
                or api_response.get("conversation", {}).get("id")
            )
            if not conversation_id:
                raise ValueError("conversation_id missing from API response")

        message_payload = api_response.get("message") or api_response
        message_text = _extract_text(message_payload)
        message_id = (
            message_payload.get("message_id")
            or message_payload.get("messageId")
            or message_payload.get("id")
            or api_response.get("message_id")
            or api_response.get("messageId")
        )

        state = (
            (message_payload.get("state") or "")
            if isinstance(message_payload, dict)
            else ""
        )
        state = state.upper()

        if conversation_id and message_id and (
            not message_text or state != "COMPLETED"
        ):
            latest = stravito_client.get_message(conversation_id, message_id)
            message_payload = latest
            message_text = _extract_text(latest)
            message_id = (
                latest.get("message_id")
                or latest.get("messageId")
                or message_id
            )

        if not message_text:
            message_text = "No response text returned from iHub."

        if isinstance(message_payload, dict):
            sources = message_payload.get("sources_extracted") or message_payload.get(
                "sources", []
            )
        else:
            sources = []

        guardrails = assess_guardrails(request, sources)

        final_text = synthesize_final_answer(
            user_prompt=request.message,
            stravito_answer=message_text,
            assessment=guardrails,
            sources=guardrails.source_flags,
        )

        if final_text:
            message_text = final_text
        elif guardrails.fabrication_warning:
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

