# MahaFlow frontend

React/Vite frontend for the SIH26130 approval intelligence backend.

## Run

```powershell
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000/api`. To change it, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

The UI has a demo fallback for the profile/checklist/scheme/document-review surfaces so it remains navigable when the backend or external services are offline. It does not expose Supabase or Ollama credentials.
