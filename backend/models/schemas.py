from pydantic import BaseModel, Field, field_validator

from config import get_settings


class AnalysisRequest(BaseModel):
    """Incoming request payload for log analysis."""

    logs: str = Field(..., min_length=1, description="Raw CI/CD logs to analyze")

    @field_validator("logs")
    @classmethod
    def validate_logs(cls, value: str) -> str:
        normalized_logs = value.strip()
        if not normalized_logs:
            raise ValueError("Logs cannot be empty.")

        max_log_chars = get_settings().max_log_chars
        if len(normalized_logs) > max_log_chars:
            raise ValueError(f"Logs cannot exceed {max_log_chars} characters.")

        return normalized_logs


class AnalysisResponse(BaseModel):
    """Structured response returned to the frontend."""

    root_cause: str
    summary: str
    fix: str
