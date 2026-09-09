# Maha Approval Intelligence API
FastAPI foundation for SIH26130. The rules engine is the eligibility authority; Qwen 2.5 via Ollama only assists with intake and explanations.

## Run locally
1. Create a Supabase project, run `schema.sql` in the SQL editor, and copy `.env.example` to `.env` with project credentials.
2. Install Python 3.12+ dependencies: `python -m venv .venv`, activate it, then `pip install -r requirements.txt`.
3. Install Ollama and pull the model: `ollama serve` and `ollama pull qwen2.5:7b`.
4. Start the API: `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000/docs`.

## Docker
`docker compose up --build`
en
In another terminal, load Qw into the Ollama container: `docker compose exec ollama ollama pull qwen2.5:7b`. Set `OLLAMA_BASE_URL=http://ollama:11434` in `.env` when running the API in Compose.

## Core endpoints
- `GET /health`
- `POST /api/profiles`
- `GET /api/profiles/{profile_id}/checklist`
- `POST /api/ai/intake`
- `POST /api/ai/explanations`
- `POST /api/ai/explanations/stream`

The seed approvals and sources are explicitly illustrative and require legal verification before production use.