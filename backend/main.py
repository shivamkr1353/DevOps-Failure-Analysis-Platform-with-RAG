import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from models.schemas import AnalysisRequest, AnalysisResponse
from services.fallback_analyzer import build_fallback_analysis
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


def format_validation_errors(exc: RequestValidationError) -> str:
    """Convert FastAPI validation details into one readable message."""

    messages: list[str] = []

    for error in exc.errors():
        message = str(error.get("msg", "Invalid request.")).strip()
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ").strip()

        if message and message not in messages:
            messages.append(message)

    if not messages:
        return "Invalid request payload."

    if len(messages) == 1:
        return messages[0]

    return " ".join(messages)


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
            headers={"Retry-After": str(retry_after)},
        )

    raw_logs = request.logs
    cleaned_logs = clean_logs(raw_logs)

    try:
        analysis = await analyze_logs(cleaned_logs, raw_logs)
        return AnalysisResponse(**analysis)
    except LLMServiceError as exc:
        logger.warning("LLM analysis failed, returning fallback analysis: %s", exc)
        fallback_analysis = build_fallback_analysis(cleaned_logs, raw_logs)
        return AnalysisResponse(**fallback_analysis)
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return readable validation messages to the frontend."""

    return JSONResponse(status_code=422, content={"detail": format_validation_errors(exc)})


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
