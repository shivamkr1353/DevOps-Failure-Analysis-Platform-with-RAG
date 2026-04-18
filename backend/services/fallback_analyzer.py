import re


PYTHON_IMPORT_ERROR_PATTERN = re.compile(
    r"(?:ModuleNotFoundError:\s*No module named|ImportError:\s*No module named)\s+['\"](?P<dependency>[^'\"]+)['\"]",
    re.IGNORECASE,
)
JS_IMPORT_ERROR_PATTERNS = [
    re.compile(r"Could not resolve\s+['\"](?P<dependency>[^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"Cannot find module\s+['\"](?P<dependency>[^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"Can't resolve\s+['\"](?P<dependency>[^'\"]+)['\"]", re.IGNORECASE),
]
TIMEOUT_PATTERNS = [
    re.compile(r"progress deadline exceeded", re.IGNORECASE),
    re.compile(r"timed out after\s+\d+", re.IGNORECASE),
    re.compile(r"context deadline exceeded", re.IGNORECASE),
    re.compile(r"readiness probe failed", re.IGNORECASE),
]
PORT_PATTERNS = [
    re.compile(r"address already in use", re.IGNORECASE),
    re.compile(r"failed to bind", re.IGNORECASE),
    re.compile(r"port\s+\d+.*already in use", re.IGNORECASE),
]
AUTH_PATTERNS = [
    re.compile(r"\b401\b"),
    re.compile(r"\b403\b"),
    re.compile(r"permission denied", re.IGNORECASE),
    re.compile(r"access denied", re.IGNORECASE),
    re.compile(r"authentication failed", re.IGNORECASE),
]


def _clip(text: str, limit: int = 180) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."


def _interesting_lines(text: str, limit: int = 3) -> list[str]:
    keywords = ("error", "failed", "failure", "exception", "timeout", "denied", "resolve")
    matches: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if any(keyword in stripped.lower() for keyword in keywords):
            matches.append(_clip(stripped))

        if len(matches) == limit:
            break

    return matches


def build_fallback_analysis(cleaned_logs: str, original_logs: str) -> dict[str, str]:
    """Produce a useful best-effort analysis when the LLM path is unavailable."""

    combined_logs = "\n".join(part for part in (cleaned_logs, original_logs) if part).strip()

    python_match = PYTHON_IMPORT_ERROR_PATTERN.search(combined_logs)
    if python_match:
        dependency = python_match.group("dependency")
        return {
            "root_cause": f"The pipeline is failing because the Python dependency '{dependency}' is missing from the environment.",
            "summary": f"The job reached an import step and crashed when Python could not load '{dependency}'.",
            "fix": f"Add '{dependency}' to requirements.txt or install it in the runtime image, then rebuild and rerun the pipeline.",
        }

    for pattern in JS_IMPORT_ERROR_PATTERNS:
        js_match = pattern.search(combined_logs)
        if js_match:
            dependency = js_match.group("dependency")
            return {
                "root_cause": f"The frontend build is failing because the JavaScript dependency '{dependency}' cannot be resolved.",
                "summary": f"The bundler reached a build step and could not find '{dependency}' in the installed frontend dependencies.",
                "fix": f"Add '{dependency}' to frontend/package.json if it is required, run a clean install, and rebuild the frontend image.",
            }

    if any(pattern.search(combined_logs) for pattern in TIMEOUT_PATTERNS):
        return {
            "root_cause": "The deployment is timing out before the service becomes healthy.",
            "summary": "The logs show a readiness or rollout deadline failure, which usually means the app is starting too slowly, crashing during boot, or not answering the health check in time.",
            "fix": "Check the container startup logs, confirm the app binds to the expected port, verify the health endpoint, and fix any boot-time crash or long-running initialization.",
        }

    if any(pattern.search(combined_logs) for pattern in PORT_PATTERNS):
        return {
            "root_cause": "The application cannot start because the target port is unavailable or the bind step is failing.",
            "summary": "The service appears to fail during startup before it can accept traffic.",
            "fix": "Make sure the app listens on the platform-provided port, avoid hard-coded conflicting ports, and check for another process already using the same port.",
        }

    if any(pattern.search(combined_logs) for pattern in AUTH_PATTERNS):
        return {
            "root_cause": "The pipeline is failing because an authenticated step does not have valid credentials or permission.",
            "summary": "The error pattern looks like an authorization failure rather than a code compilation problem.",
            "fix": "Verify the required secrets, tokens, and service permissions for the failing environment, then rerun the job after rotating or correcting them if needed.",
        }

    highlighted_lines = _interesting_lines(cleaned_logs or original_logs)
    highlighted_text = " ".join(highlighted_lines).strip()

    if highlighted_text:
        return {
            "root_cause": f"The most likely failure point is: {highlighted_text}",
            "summary": "The automatic fallback analyzer could not use the LLM, so it highlighted the most suspicious error lines from the CI/CD output.",
            "fix": "Start from the failing command and the highlighted error lines, then verify the missing dependency, configuration, or startup condition they point to.",
        }

    return {
        "root_cause": "The pipeline is failing, but the available log excerpt does not expose one clear root cause.",
        "summary": "The fallback analyzer could not find a strong signature in the provided logs.",
        "fix": "Retry with a slightly larger log excerpt that includes the first stack trace or the command that failed immediately before the pipeline stopped.",
    }
