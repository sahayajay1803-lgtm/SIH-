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
- `POST /api/ai/intake`
- `GET /api/ai/status`
- `POST /api/ai/explanations`
- `POST /api/ai/explanations/stream`

Explanation requests use the local retrieval layer in `app/services/rag.py` to add source-labelled context for the selected approval before calling Ollama Cloud. The current chunks are illustrative placeholders; replace them with verified official material before production use.

The seed approvals and sources are explicitly illustrative and require legal verification before production use.