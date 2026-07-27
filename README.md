# Placed MVP

Placed is an MVP for automated frame and mat recommendations from an uploaded artwork image.

The project is organized as a monorepo:

```text
backend/   FastAPI API, recommendation algorithm, preview renderer
frontend/  React + Vite + TypeScript browser UI
```

## Run Backend

```powershell
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## Run Frontend

```powershell
cd frontend
pnpm install
pnpm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

The frontend expects the backend at `http://127.0.0.1:8000`.
To override it, set:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Repository Shape

For now, keep frontend and backend in one private GitHub repository. The algorithm, renderer, API contract, and UI are still changing together, so a monorepo is simpler and safer.

Separate repositories only become useful when frontend and backend have independent teams, release cycles, permissions, or deployment pipelines.
