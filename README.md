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

## Timeweb Cloud Deployment

The current working deployment uses Timeweb Cloud App Platform without Docker.

### Backend

Create a backend app with:

```text
Type: Backend
Framework: Python / FastAPI
Environment: Python 3.12
Project directory: /backend
Build command: pip3 install --upgrade -r requirements.txt
Dependencies: leave empty
Start command: uvicorn main:app --host 0.0.0.0 --port 8000
Health check path: /
Branch: main
```

Current backend technical domain:

```text
https://urluri-placed-aac7.twc1.net
```

Health check:

```powershell
curl.exe https://urluri-placed-aac7.twc1.net/
```

Expected response:

```json
{"status":"ok","service":"placed-api"}
```

### Frontend

Create a frontend app with:

```text
Type: Frontend
Framework: React
Environment: Node.js 22
Project directory: /frontend
Build command: pnpm run build
Build directory: dist
Dependencies: leave empty
Start command: not needed
Branch: main
```

Frontend build environment variable:

```text
VITE_API_BASE_URL=https://urluri-placed-aac7.twc1.net
```

After the frontend app receives its technical domain, add it to the backend environment:

```text
FRONTEND_ORIGIN=https://YOUR_FRONTEND_DOMAIN
```

Then redeploy the backend so browser requests are allowed by CORS.

### Production Checks

Check backend:

```powershell
curl.exe https://urluri-placed-aac7.twc1.net/
```

Check recommendations:

```powershell
curl.exe -X POST https://urluri-placed-aac7.twc1.net/api/recommend `
  -F "widthMm=300" `
  -F "heightMm=400" `
  -F "artworkType=poster" `
  -F "interiorStyle=minimal"
```

Check render output:

```powershell
curl.exe -L -o placed-render.jpg -X POST https://urluri-placed-aac7.twc1.net/api/render `
  -F "widthMm=300" `
  -F "heightMm=400" `
  -F "artworkType=poster" `
  -F "interiorStyle=minimal"
```
