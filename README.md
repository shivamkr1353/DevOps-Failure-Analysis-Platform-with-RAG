# LLM-Powered DevOps Failure Analysis System

A full-stack project that analyzes CI/CD logs with an LLM and returns:

- Root cause
- Summary
- Fix suggestion

## Tech Stack

- Backend: FastAPI
- Frontend: React + Vite
- LLM: OpenAI API
- Styling: Tailwind CSS
- Deployment: Docker + Render blueprint

## Project Structure

```text
root/
  backend/
    main.py
    requirements.txt
    .env.example
    models/
      __init__.py
      schemas.py
    services/
      __init__.py
      fallback_analyzer.py
      log_cleaner.py
      llm_service.py

  frontend/
    package.json
    .env.example
    index.html
    postcss.config.js
    tailwind.config.js
    vite.config.js
    src/
      main.jsx
      App.jsx
      index.css
      data/
        sampleLogs.js
      components/
        LogInput.jsx
        ResultCard.jsx
```

## What The App Does

1. User pastes CI/CD logs into the frontend.
2. Frontend sends them to `POST /analyze`.
3. Backend cleans the logs by focusing on failure-heavy lines.
4. Backend sends the cleaned logs to OpenAI.
5. API returns:
   - `root_cause`
   - `summary`
   - `fix`

If the provider is unavailable, the backend falls back to a built-in heuristic analyzer so the user still gets a useful diagnosis instead of a generic upstream failure.

## Local Backend Setup

```bash
cd backend
python -m venv ..\.venv
..\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Update `.env` with your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4-mini
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
MAX_LOG_CHARS=20000
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
SERVE_FRONTEND=true
```

Run the backend:

```bash
cd backend
..\.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```

API will be available at `http://localhost:8000`.

## Local Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend will run at `http://localhost:5173`.

The frontend also supports a matching local validation limit:

```env
VITE_MAX_LOG_CHARS=20000
```

## Public Deployment Readiness

This repo now includes a safer starter setup for public use:

- OpenAI keys stay on the backend only.
- The backend rate-limits `/analyze` requests.
- Log submissions are capped by `MAX_LOG_CHARS`.
- Raw provider errors are not exposed to the browser.
- The backend can serve the built React app in production, so frontend and API can run from one public URL.
- Docker and `render.yaml` are included for a simple GitHub-to-Render deployment path.

## Deploy On Render

This project is configured to deploy as a single Docker-based web service on Render.

1. Push the repo to GitHub.
2. In Render, create a new Blueprint and point it at the GitHub repo.
3. Render will read `render.yaml` from the repo root.
4. Add your real `OPENAI_API_KEY` in Render when prompted.
5. Deploy the service and wait for the `/health` check to pass.

The app will then be available from one public URL, and the React frontend will call the FastAPI backend on the same origin.

## Docker Run

You can also run the production build locally with Docker:

```bash
docker build -t devops-failure-analysis .
docker run -p 8000:8000 --env OPENAI_API_KEY=your_api_key_here devops-failure-analysis
```

Then open `http://localhost:8000`.

## Example API Request

**Endpoint**

```http
POST http://localhost:8000/analyze
Content-Type: application/json
```

**Request Body**

```json
{
  "logs": "ERROR: ModuleNotFoundError: No module named 'requests'"
}
```

**Response**

```json
{
  "root_cause": "The build is failing because the Python dependency 'requests' is missing from the environment or requirements file.",
  "summary": "The CI pipeline reached the test or runtime step and crashed when the application tried to import 'requests'.",
  "fix": "Add 'requests' to requirements.txt, rebuild the environment, and rerun the pipeline."
}
```

## Sample Logs Included In The Frontend

- Missing dependency
- Docker build failure
- Timeout error

## Notes

- No LangChain is used.
- The backend uses the OpenAI Python SDK directly.
- The app defaults to `gpt-5.4-mini`, which is a good balance of quality, speed, and cost for this use case.
- If the model returns invalid JSON, the backend raises a clean API error.
- If the provider request fails, the backend returns a best-effort heuristic analysis instead of a temporary provider error.
- For local development, keep the frontend and backend separate.
- For public deployment, this repo is set up to serve the built frontend from FastAPI through Docker.
