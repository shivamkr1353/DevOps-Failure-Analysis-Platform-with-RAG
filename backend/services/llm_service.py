import json
import re
from typing import Any

from openai import AsyncOpenAI

from config import get_settings

SYSTEM_PROMPT = """You are a DevOps expert.
Analyze CI/CD failure logs and return only valid JSON with this exact shape:
{
  "root_cause": "",
  "summary": "",
  "fix": ""
}

Rules:
- Be concise and practical.
- Focus on the most likely root cause.
- Do not wrap the JSON in markdown.
- Do not include extra keys.
"""


class LLMServiceError(Exception):
    """Raised when the OpenAI integration fails."""


def get_client() -> AsyncOpenAI:
    """Create an async OpenAI client from environment variables."""

    api_key = get_settings().openai_api_key
    if not api_key:
        raise LLMServiceError("OPENAI_API_KEY is not set. Add it to backend/.env before running the API.")

    return AsyncOpenAI(api_key=api_key)


def build_user_prompt(cleaned_logs: str, original_logs: str) -> str:
    """Build the user prompt sent to the LLM."""

    original_excerpt = "\n".join(original_logs.splitlines()[:80]).strip()

    return f"""Analyze the following CI/CD logs and return JSON.

Cleaned logs:
{cleaned_logs}

Original log excerpt:
{original_excerpt}
"""


def extract_text_from_response(response: Any) -> str:
    """Read plain text from the Responses API object."""

    if getattr(response, "output_text", None):
        return response.output_text

    chunks: list[str] = []

    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text_value = getattr(content, "text", None)
            if text_value:
                chunks.append(text_value)

    return "\n".join(chunks).strip()


def parse_json_payload(raw_output: str) -> dict[str, str]:
    """Parse the JSON returned by the model."""

    candidates = [raw_output.strip()]
    json_match = re.search(r"\{[\s\S]*\}", raw_output)
    if json_match:
        candidates.insert(0, json_match.group(0))

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    else:
        raise LLMServiceError("The model returned an invalid JSON response.")

    result = {
        "root_cause": str(payload.get("root_cause", "")).strip(),
        "summary": str(payload.get("summary", "")).strip(),
        "fix": str(payload.get("fix", "")).strip(),
    }

    if not all(result.values()):
        raise LLMServiceError("The model response was missing one or more required fields.")

    return result


async def analyze_logs(cleaned_logs: str, original_logs: str) -> dict[str, str]:
    """Send cleaned logs to OpenAI and return the parsed analysis."""

    client = get_client()
    model_name = get_settings().openai_model

    try:
        response = await client.responses.create(
            model=model_name,
            reasoning={"effort": "low"},
            max_output_tokens=350,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_user_prompt(cleaned_logs, original_logs),
                        }
                    ],
                },
            ],
        )
    except Exception as exc:
        raise LLMServiceError(f"OpenAI request failed: {exc}") from exc

    raw_output = extract_text_from_response(response)
    if not raw_output:
        raise LLMServiceError("The model returned an empty response.")

    return parse_json_payload(raw_output)
