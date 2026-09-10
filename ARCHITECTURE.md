# Backend and AI Architecture

## Goal

This backend operationalizes the SRS goal: help Maharashtra entrepreneurs discover, explain, prepare, and track industrial approvals while preserving MAITRI as the future legal system of record.

## 1. Architecture Overview

The selected backend is **Python 3.12 + FastAPI**. FastAPI gives typed request contracts, async I/O for Ollama Cloud, and OpenAPI documentation at `/docs`.

Flow:

`React client -> FastAPI -> Supabase Postgres/Storage`

`FastAPI -> deterministic rules engine -> checklist`

`FastAPI -> Ollama Cloud (gemma4:31b-cloud) -> intake clarification or explanation only`

`FastAPI -> MaitriAdapter interface -> mock now, real MAITRI adapter later`

Supabase is the system of record for profiles, approvals, checklist items, documents, notifications, and audit events. Supabase Storage should hold document bytes; database rows hold metadata and validation state. Row Level Security must be enabled before production data is used.

The rules engine is intentionally local and deterministic. The model cannot decide eligibility. Gemma receives only the profile facts and an already-selected approval when generating explanations. Every explanation returns the approval's source, including the explicit illustrative placeholder status.

### Bottlenecks and concurrency

- **Cloud model rate limits/inference:** requests are gated by `LLM_MAX_CONCURRENCY` (default 4) with an `asyncio.Semaphore`. Extra requests wait instead of creating an unbounded burst.
- **Long generation:** `LLM_TIMEOUT_SECONDS` bounds the request. Routes return HTTP 503 when Ollama Cloud is unavailable.
- **Supabase round trips:** keep checklist eligibility in-process and use indexed profile/status columns. Move heavy analytics to SQL views or background jobs later.
- **Large files:** upload directly to Supabase Storage using signed URLs in the next slice; never proxy large document bytes through the API.
- **Horizontal scaling:** the in-process semaphore is per instance. For multiple API replicas, add a shared queue/worker or an Ollama pool and rate limit at the gateway.

## 2. Data Models and Database Schema

`schema.sql` defines the initial Supabase schema:

- `business_profiles`: structured intake facts and ownership.
- `approvals`: data-driven approval metadata, source, SLA, and dependencies.
- `checklist_items`: a profile-specific approval instance and workflow status.
- `documents`: Supabase Storage path, MIME type, metadata, and basic validation state.
- `notifications`: in-app/email events and read state.

The SRS's `audit_logs` and official analytics views should be added before the demo grows beyond the primary journey. For production, `user_id` should reference Supabase Auth users and RLS policies should enforce entrepreneur ownership plus official read access.

The Python Pydantic models in `app/schemas.py` validate API boundaries. The schema is intentionally SQL-first because Supabase owns migrations and Postgres is the source of truth.

## 3. REST API Design

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Runtime/configuration health |
| POST | `/api/profiles` | Persist an entrepreneur business profile |
| GET | `/api/profiles/{profile_id}/checklist` | Evaluate deterministic rules and return checklist |
| POST | `/api/ai/intake` | Clarify free text and extract explicit profile fields |
| POST | `/api/ai/explanations` | Explain one already-selected approval |
| POST | `/api/ai/explanations/stream` | Stream an explanation as plain text |

Next endpoints to add for the rest of the MVP are `POST /api/documents/{item_id}`, `POST /api/maitri/submit`, `GET /api/status/{profile_id}`, `GET /api/official/applications`, and `GET /api/official/analytics`.

The current implementation now also exposes `GET /api/schemes`, `GET /api/profiles/{profile_id}/schemes`, `POST /api/ai/documents/review`, and `POST /api/maitri/submit`. Scheme data is an illustrative central/state catalogue for the frontend. Document review accepts PDF/JPG/PNG up to 10 MB, extracts PDF text, asks the configured model for a scored constructive review, and returns a review ID. The MAITRI route consumes that review ID through a clearly simulated adapter; it does not contact the real MAITRI portal.

The AI endpoints are not authorization bypasses: authentication, ownership checks, request quotas, and audit logging should be placed in dependencies before connecting a frontend to them.

## 4. Ollama Cloud Integration Strategy

`app/services/llm.py` calls the OpenAI-compatible `POST {OLLAMA_BASE_URL}/chat/completions` endpoint with `model=gemma4:31b-cloud`, system/user messages, `stream`, and low temperature. The client sends `Authorization: Bearer {OLLAMA_API_KEY}` and translates connection, timeout, and HTTP errors to a stable `LLMUnavailable` exception.

The intake system prompt requires JSON with `reply`, `extracted_fields`, and `missing_fields`. It says to extract only explicit facts and ask clarification instead of guessing. The API validates that response with Pydantic.

The explanation system prompt receives a JSON context containing the profile and a rule-engine-selected approval. It forbids changing eligibility, inventing thresholds, and unsupported legal advice. The API returns the rule source separately, so source provenance does not depend on model behavior.

Streaming consumes OpenAI-compatible `data: {json}` chunks. The client yields only content deltas and FastAPI exposes them through `StreamingResponse`. Use `text/plain` for the MVP. SSE with event IDs can be added when the frontend needs reconnectable streams.

## 5. Core Implementation

- `app/main.py`: FastAPI initialization, CORS, health endpoint.
- `app/api.py`: profile, checklist, intake, explanation, and streaming controllers.
- `app/services/rules.py`: illustrative data-driven rules. Replace seed conditions and sources only after legal verification.
- `app/services/rag.py`: source-labelled retrieval over the current illustrative approval knowledge chunks.
- `app/services/supabase.py`: Supabase client and profile persistence boundary.
- `app/services/llm.py`: bounded, timeout-aware Ollama Cloud client.
- `app/schemas.py`: typed API contracts.

The AI layer is deliberately not used by `evaluate_profile`. This is the main safety and correctness boundary from the SRS.

Explanation generation uses retrieval-augmented context after `find_approval` has selected an approval. Retrieval is scoped to that approval and cannot make eligibility decisions. The initial implementation uses dependency-free lexical matching; replace `KNOWLEDGE_BASE` with verified, versioned source documents and an embedding/vector store when the corpus is available.

## 6. Setup and Deployment

### Hosted Supabase plus local services

1. Create a Supabase project.
2. Run `schema.sql` in its SQL editor.
3. Copy `.env.example` to `.env`, then set `SUPABASE_URL` and `SUPABASE_KEY`.
4. Local Python path: install Python 3.12+, set `OLLAMA_API_KEY`, run `pip install -r requirements.txt`, and start `uvicorn app.main:app --reload`.
5. Docker path: set `OLLAMA_API_KEY` in `.env`, then run `docker compose up --build`.

Supabase is a managed database service, so it is not duplicated in this Compose file. The Compose stack starts only the API and connects it to Supabase and Ollama Cloud. A fully local Supabase stack should be started with the Supabase CLI (`supabase start`) when local Postgres/Auth/Storage emulation is required.

### Production hardening

Add Supabase Auth JWT verification, RLS, MIME/content scanning, signed Storage URLs, rate limiting, structured logs, audit events, a queue for AI jobs, and a real MAITRI adapter only after the government API contract is confirmed.
