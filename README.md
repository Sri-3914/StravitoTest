# Stravito Guarded Chat

This project delivers a guardrail-enabled chat experience backed by Stravito’s iHub Assistant. It consists of:

- A **FastAPI** backend that proxies chat requests to iHub, enforces business guardrails, and normalises responses.
- A **React + Tailwind CSS** frontend that recreates the iHub Assistant interface with transparency on evidence strength, market scope, and sources.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Access credentials for the iHub Assistant API (`IHUB_API_KEY`, `IHUB_BASE_URL`)

## Backend Setup

```bash
cd /Users/sunil/StravitoTest/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env  # populate with your secrets
uvicorn app.main:app --reload
```

### Mock Mode

To run the backend without real iHub credentials, enable the built-in mock responses:

```bash
export IHUB_USE_MOCK=true
export AZURE_OPENAI_ENABLED=false
uvicorn app.main:app --reload
```

When `IHUB_USE_MOCK` is true (default is false), the backend generates deterministic conversation responses and sample citations so the UI and guardrails can be exercised offline.

### Guardrail Coverage

- **Prompt completion**: verifies market, category, and timeframe are provided; otherwise responds with clarifying questions.
- **Evidence confidence**: labels responses as `strong data`, `limited data`, or `no direct evidence` based on source quality and recency.
- **Source vetting**: flags sources older than three years and distinguishes contextual references from empirical evidence.
- **Market & category scope**: reiterates the focus requested and highlights the weighting across priority markets (U.S., Mexico, Brazil).
- **Fabrication safeguard**: if no direct evidence exists, the assistant states the limitation and offers only a framework-level response.
- **Azure OpenAI synthesis**: every Stravito response and guardrail assessment is post-processed by an Azure OpenAI deployment to deliver the final, policy-compliant answer.

## Frontend Setup

```bash
cd /Users/sunil/StravitoTest/frontend
npm install
npm run dev
```

The Vite dev server proxies API requests to `http://127.0.0.1:8000`.

## Project Structure

```
backend/
  app/
    main.py            # FastAPI entry point
    schemas.py         # Pydantic models shared across endpoints
    services/          # Stravito client integration
    utils/             # Guardrail logic
frontend/
  src/                 # React application with Tailwind styling
```

## Tests & Verification

- Manual: run `curl http://127.0.0.1:8000/health` to confirm backend is live.
- Frontend: interact via `npm run dev` and check guardrail badges update as responses arrive.