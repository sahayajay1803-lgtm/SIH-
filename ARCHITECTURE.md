# Backend and AI Architecture

## Goal

This backend operationalizes the SRS goal: help Maharashtra entrepreneurs discover, explain, prepare, and track industrial approvals while preserving MAITRI as the future legal system of record.

## 1. Architecture Overview

The selected backend is **Python 3.12 + FastAPI**. FastAPI gives typed request contracts, async I/O for Ollama, and OpenAPI documentation at `/docs`.

Flow:

`React client -> FastAPI -> Supabase Postgres/Storage`

`FastAPI -> deterministic rules engine -> checklist`

`FastAPI -> Ollama/Qwen 2.5 -> intake clarification or explanation only`

`FastAPI -> MaitriAdapter interface -> mock now, real MAITRI adapter later`

Supabase is the system of record for profiles, approvals, checklist items, documents, notifications, and audit events. Supabase Storage should hold document bytes; database rows hold metadata and validation state. Row Level Security must be enabled before production data is used.

The rules engine is intentionally local and deterministic. The model cannot decide eligibility. Ollama receives only the profile facts and an already-selected approval when generating explanations. Every explanation returns the approval's source, including the explicit illustrative placeholder status.

### Bottlenecks and concurrency

- **Ollama model loading/inference:** requests are gated by `OLLAMA_MAX_CONCURRENCY` (default 2) with an `asyncio.Semaphore`. Extra requests wait instead of spawning unbounded model work.
- **Long generation:** `OLLAMA_TIMEOUT_SECONDS` bounds the request. Routes return HTTP 503 for a model that is unavailable or still loading.
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

The AI endpoints are not authorization bypasses: authentication, ownership checks, request quotas, and audit logging should be placed in dependencies before connecting a frontend to them.

## 4. Ollama Integration Strategy

`app/services/ollama.py` calls `POST {OLLAMA_BASE_URL}/api/generate` with `model`, `system`, `prompt`, `stream`, and low temperature. The client catches connection, timeout, and HTTP errors and translates them to a stable `OllamaUnavailable` exception.

The intake system prompt requires JSON with `reply`, `extracted_fields`, and `missing_fields`. It says to extract only explicit facts and ask clarification instead of guessing. The API validates that response with Pydantic.

The explanation system prompt receives a JSON context containing the profile and a rule-engine-selected approval. It forbids changing eligibility, inventing thresholds, and unsupported legal advice. The API returns the rule source separately, so source provenance does not depend on model behavior.

Streaming uses Ollama's newline-delimited JSON response. The client yields only `response` token fragments and stops at `done`; FastAPI exposes these fragments through `StreamingResponse`. Use `text/plain` for the MVP. SSE with event IDs can be added when the frontend needs reconnectable streams.

## 5. Core Implementation

- `app/main.py`: FastAPI initialization, CORS, health endpoint.
- `app/api.py`: profile, checklist, intake, explanation, and streaming controllers.
- `app/services/rules.py`: illustrative data-driven rules. Replace seed conditions and sources only after legal verification.
- `app/services/supabase.py`: Supabase client and profile persistence boundary.
- `app/services/ollama.py`: bounded, timeout-aware Ollama client.
- `app/schemas.py`: typed API contracts.

The AI layer is deliberately not used by `evaluate_profile`. This is the main safety and correctness boundary from the SRS.

## 6. Setup and Deployment

### Hosted Supabase plus local services

1. Create a Supabase project.
2. Run `schema.sql` in its SQL editor.
3. Copy `.env.example` to `.env`, then set `SUPABASE_URL` and `SUPABASE_KEY`.
4. Local Python path: install Python 3.12+, run `pip install -r requirements.txt`, then `ollama serve`, `ollama pull qwen2.5:7b`, and `uvicorn app.main:app --reload`.
5. Docker path: run `docker compose up --build`, then `docker compose exec ollama ollama pull qwen2.5:7b`.

Supabase is a managed database service, so it is not duplicated in this Compose file. The Compose stack starts the API and Ollama and connects the API to the hosted Supabase URL. A fully local Supabase stack should be started with the Supabase CLI (`supabase start`) when local Postgres/Auth/Storage emulation is required; that stack is intentionally separate because Supabase bundles several services, not just Postgres.

### Production hardening

Add Supabase Auth JWT verification, RLS, MIME/content scanning, signed Storage URLs, rate limiting, structured logs, audit events, a queue for AI jobs, and a real MAITRI adapter only after the government API contract is confirmed.
