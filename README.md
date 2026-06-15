# DevOps Failure Analysis Platform with RAG

A full-stack AIOps platform that analyzes CI/CD failure logs with AI, tracks historical incidents, and retrieves similar past failures using RAG (Retrieval-Augmented Generation). 

This platform streamlines the debugging process for DevOps and engineering teams by automatically diagnosing build failures, tracking historical data, and providing actionable fixes.

**[Live Demo](https://llm-powered-devops-failure-analysis.onrender.com/)**

## Key Features

1. **GitHub Actions Integration** — Connect repositories and automatically analyze failed workflow runs.
2. **AI-Powered Diagnostics** — Paste logs from any CI/CD platform and get instant root cause analysis and suggested fixes via Google's Gemini API.
3. **RAG-Powered Similarity Search** — Automatically retrieves similar past failures using ChromaDB to improve analysis accuracy and consistency.
4. **Failure History Tracking** — Persistent tracking and searching of all historical failure analyses using SQLite.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12) |
| **Frontend** | React 18 + Vite |
| **Styling** | Tailwind CSS 3 |
| **LLM Engine** | Gemini API (structured output) |
| **RAG & Vector DB** | ChromaDB with `all-MiniLM-L6-v2` embeddings |
| **Database** | SQLite via `aiosqlite` |
| **Integrations** | GitHub API via `httpx` (async HTTP) |
| **Deployment** | Docker + Render |

## Design Decisions & Technical Highlights

- **Zero-Bloat AI Integration**: No heavy frameworks like LangChain are used. The backend interacts directly with Gemini's structured-output API via the official `google-genai` SDK for maximum performance and predictability.
- **Repository Pattern**: Database operations are abstracted using the repository pattern, allowing for seamless future migration from SQLite to PostgreSQL.
- **Resilient Architecture**: All external dependencies feature graceful degradation. If the Vector DB is unavailable or the LLM provider experiences downtime, the system falls back to heuristic analysis or standard LLM requests to ensure continuous availability.
- **Local Embeddings**: The RAG pipeline uses `all-MiniLM-L6-v2` running locally on the CPU, eliminating external API costs and latency for vector embeddings.

## Architecture & Pipeline

### Analysis Pipeline

The system uses a unified pipeline for both manual log analysis and automated GitHub Actions analysis:

```text
Incoming Logs
  ↓
Clean Logs (remove noise, isolate error signatures)
  ↓
Retrieve Similar Failures (ChromaDB RAG, top 3 by L2 distance)
  ↓
Build Enriched Prompt (current context + historical similar failures)
  ↓
Gemini LLM Analysis (enforces structured JSON output)
  ↓
Store Incident (SQLite) & Store Embedding (ChromaDB)
  ↓
Return Actionable Response
```

### Database & RAG Architecture
- **Vector DB**: Persistent ChromaDB with local filesystem storage. Each analyzed failure is stored as an embedding combining the cleaned log text, root cause, and fix suggestion.
- **Relational DB**: SQLite tracks incidents with fields for workflow name, run ID, source type, logs, root cause, and timestamps.
- **Auto-initialization**: Tables and collections are created on app startup via the FastAPI lifespan context manager.

## Project Structure

```text
root/
  backend/
    main.py                          # FastAPI application entry point
    models/                          # Pydantic request/response schemas
    services/                        # Core business logic (LLM, RAG, GitHub, Cleaning)
    database/                        # SQLite schema and repository pattern implementation
    rag/                             # ChromaDB client, embeddings, and retrieval
    routes/                          # API endpoints (GitHub, History, Analysis)

  frontend/
    src/
      components/                    # React components (Dashboard, Modals, Panels)
      api.js                         # Centralized API client
      index.css                      # Global styling
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| **GET** | `/health` | Application health check |
| **POST** | `/analyze/enriched` | Analyze logs using LLM and RAG similarity |
| **GET** | `/github/workflows` | List workflows for a given GitHub repository |
| **GET** | `/github/runs/failed` | Retrieve failed workflow runs |
| **POST** | `/github/analyze-run/{id}` | Analyze a specific GitHub Actions run |
| **GET** | `/history` | Retrieve paginated failure history |
| **GET** | `/history/{id}` | Get details of a specific incident |

## Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 18+
- GitHub Personal Access Token (Fine-grained with `Actions: Read-only` or Classic with `repo` scope)
- Gemini API Key

### Windows Setup (Automated)
If you are on Windows, you can launch both the frontend and the backend automatically using the `run.bat` script:

1. **Environment Variables**:
   - Copy `backend/.env.example` to `backend/.env` and add your `GEMINI_API_KEY` and `GITHUB_TOKEN`.
   - Copy `frontend/.env.example` to `frontend/.env`.
2. **Install Dependencies**:
   ```bash
   cd backend && python -m venv ..\.venv && ..\.venv\Scripts\python -m pip install -r requirements.txt
   cd ../frontend && npm install
   cd ..
   ```
3. **Run Application**:
   ```bash
   .\run.bat
   ```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Configure your .env file
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Docker Deployment

The project is fully containerized for easy deployment. The configuration includes persistent volume mounts for the database and vector store.

```bash
docker build -t devops-failure-analysis .
docker run -p 8000:8000 \
  -v devops-data:/app/backend/data \
  --env GEMINI_API_KEY=your_key \
  --env GITHUB_TOKEN=your_token \
  devops-failure-analysis
```
