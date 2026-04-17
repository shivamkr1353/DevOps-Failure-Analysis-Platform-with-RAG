import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from models.schemas import AnalysisRequest, AnalysisResponse
from services.llm_service import LLMServiceError, analyze_logs
from services.log_cleaner import clean_logs
from services.rate_limiter import InMemoryRateLimiter

settings = get_settings()
logger = logging.getLogger("failure_analysis_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LLM-Powered DevOps Failure Analysis System",
    version="1.0.0",
)

rate_limiter = InMemoryRateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health endpoint for local testing."""

    return {"status": "ok", "environment": settings.environment}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_failure(request: AnalysisRequest, http_request: Request) -> AnalysisResponse:
    """Analyze CI/CD logs and return a structured diagnosis."""

    client_host = http_request.client.host if http_request.client else "anonymous"
    allowed, retry_after = rate_limiter.is_allowed(f"analyze:{client_host}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many analysis requests. Try again in {retry_after} seconds.",
        )

    raw_logs = request.logs
    cleaned_logs = clean_logs(raw_logs)

    try:
        analysis = await analyze_logs(cleaned_logs, raw_logs)
        return AnalysisResponse(**analysis)
    except LLMServiceError as exc:
        if "OPENAI_API_KEY" in str(exc):
            logger.exception("Missing OpenAI configuration.")
            raise HTTPException(
                status_code=500,
                detail="The server is missing required configuration.",
            ) from exc

        logger.warning("LLM analysis failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The analysis provider is temporarily unavailable. Please try again.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected server error while analyzing logs.")
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error while analyzing logs.",
        ) from exc


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Return consistent JSON errors to the frontend."""

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


frontend_dist_dir = settings.frontend_dist_dir
frontend_index_path = frontend_dist_dir / "index.html"
frontend_assets_dir = frontend_dist_dir / "assets"

if settings.serve_frontend and frontend_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets_dir), name="frontend-assets")


if settings.serve_frontend and frontend_index_path.exists():

    @app.get("/", include_in_schema=False)
    async def serve_frontend_index() -> FileResponse:
        return FileResponse(frontend_index_path)


    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str) -> FileResponse:
        candidate_path = (frontend_dist_dir / full_path).resolve()
        frontend_root = frontend_dist_dir.resolve()

        if candidate_path.is_file() and Path(candidate_path).is_relative_to(frontend_root):
            return FileResponse(candidate_path)

        return FileResponse(frontend_index_path)
