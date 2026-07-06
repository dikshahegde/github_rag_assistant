# GitHub Repository RAG Assistant

A Repository QA & RAG assistant. Paste any public GitHub repository URL, load its source files, ask technical questions (e.g. "how does authentication work?", "explain user flows"). The assistant responds with markdown explanations with referenced file inline and highlight the exact code ranges.

## Prerequisites

1. **Python 3.10+** (if running locally)
2. **Node.js 18+** & **npm** (if running locally)
3. **Git client** installed in the PATH (GitPython binds to the system git)
4. A **Gemini API Key** (obtainable from Google AI Studio)

---

## Local Setup (without Docker)

### 1. Environment Variables
Copy the template and fill in your own key — never commit the real `.env` file:
```bash
cp .env.example .env
```
```env
GEMINI_API_KEY=your_gemini_api_key_here
HOST=127.0.0.1
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173
```

### 2. Run Backend
Install python dependencies:
```bash
pip install -r requirements.txt
```
Launch the FastAPI server:
```bash
python -m app.main
```

### 3. Run Frontend
Navigate to the frontend folder, install packages, and boot Vite:
```bash
cd frontend
npm install
npm run dev
```

---

## Running with Docker Compose (Development)

Preserves the original hot-reload workflow (bind-mounted source, Vite dev server):
```bash
docker compose -f docker-compose.dev.yml up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## Running with Docker Compose (Production)

Builds an optimized backend image (gunicorn + uvicorn workers, non-root user, healthcheck)
and a static frontend bundle served by nginx. No source bind-mounts.

```bash
cp .env.example .env   # fill in GEMINI_API_KEY and ALLOWED_ORIGINS
docker compose up --build -d
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (served by nginx on container port 80)

Configuration:
- `GEMINI_API_KEY` and `ALLOWED_ORIGINS` are read from `.env` by the backend container.
- `VITE_API_BASE_URL` (root `.env` or shell env) is baked into the frontend build at
  image-build time, since it's a static SPA. Set it to your public backend URL when
  deploying frontend and backend on different hosts, e.g.:
  ```bash
  VITE_API_BASE_URL=https://api.example.com docker compose up --build -d
  ```
- Ingested repositories, the vector store, and chat history persist in the
  `backend_data` named Docker volume across restarts.
- Set `ALLOWED_ORIGINS` to your real frontend origin(s) in production instead of `*`.

---

## Running Automated Tests

Run backend unit tests for chunking, API endpoints, and database interfaces:
```bash
pytest
```
