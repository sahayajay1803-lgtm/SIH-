# Maha Approval Intelligence API
FastAPI foundation for SIH26130. The rules engine is the eligibility authority; Ollama Cloud with `gemma4:31b-cloud` only assists with intake and explanations.

## Run locally
1. Create a Supabase project, run `schema.sql` in the SQL editor, and copy `.env.example` to `.env` with project credentials.
2. Install Python 3.12+ dependencies: `python -m venv .venv`, activate it, then `pip install -r requirements.txt`.
3. Add your Ollama Cloud API key to `.env` as `OLLAMA_API_KEY=...`.
4. Start the API: `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000/docs`.

## Docker
`docker compose up --build`

## Core endpoints
- `GET /health`
- `POST /api/profiles`
- `GET /api/profiles/{profile_id}/checklist`
- `GET /api/schemes`
- `GET /api/profiles/{profile_id}/schemes`
- `POST /api/ai/intake`
- `GET /api/ai/status`
- `POST /api/ai/explanations`
- `POST /api/ai/explanations/stream`
- `POST /api/ai/documents/review`
- `POST /api/maitri/submit`

Explanation requests use the local retrieval layer in `app/services/rag.py` to add source-labelled context for the selected approval before calling Ollama Cloud. The current chunks are illustrative placeholders; replace them with verified official material before production use.

The seed approvals and sources are explicitly illustrative and require legal verification before production use.

The schemes endpoint provides a filterable mock catalogue of central and Maharashtra state schemes for the frontend. Scheme records include benefit, eligibility, required-document, source, and last-verified fields. They are demo records and must be replaced or verified before production.

Document review accepts PDF/JPG/PNG uploads up to 10 MB. PDFs have text extracted with `pypdf`; images are accepted but OCR is explicitly unavailable in this MVP. The review is AI-assisted pre-validation, not legal approval. MAITRI submission is simulated and clearly labelled.