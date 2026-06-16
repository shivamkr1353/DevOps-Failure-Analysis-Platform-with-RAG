"""GitHub Actions integration — fetch workflows, runs, and logs via REST API."""

from __future__ import annotations

import io
import logging
import re
import zipfile

import httpx

from config import get_settings

logger = logging.getLogger("failure_analysis_api")

GITHUB_API_BASE = "https://api.github.com"
REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


class GitHubServiceError(Exception):
    """Raised when a GitHub API operation fails."""


def _validate_repo_params(owner: str, repo: str) -> None:
    """Validate owner and repo names to prevent injection."""

    if not owner or not REPO_NAME_PATTERN.match(owner):
        raise GitHubServiceError(f"Invalid repository owner: '{owner}'")
    if not repo or not REPO_NAME_PATTERN.match(repo):
        raise GitHubServiceError(f"Invalid repository name: '{repo}'")


def _build_headers(custom_token: str | None = None) -> dict[str, str]:
    """Build request headers, optionally including auth token."""

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "LLM-DevOps-Failure-Analyzer",
    }

    token = custom_token or get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _handle_github_error(
    response: httpx.Response,
    owner: str,
    repo: str,
    custom_token_used: bool,
    run_id: int | None = None,
) -> None:
    """Analyze a failed GitHub API response and raise a precise GitHubServiceError."""

    status = response.status_code
    if status == 200:
        return

    # Check for common GitHub API error responses
    detail = ""
    try:
        data = response.json()
        if isinstance(data, dict) and "message" in data:
            detail = f" (GitHub message: {data['message']})"
    except Exception:
        pass

    token_type = "custom Personal Access Token" if custom_token_used else "server GITHUB_TOKEN"

    if status == 301:
        raise GitHubServiceError(
            f"Repository '{owner}/{repo}' has been moved or renamed (301 Moved Permanently).{detail} "
            "Please verify the current owner and repository name on GitHub and try again."
        )

    if status == 401:
        raise GitHubServiceError(
            f"GitHub authentication failed. Your {token_type} is invalid or expired.{detail} "
            "Please check, update, or clear the token."
        )

    elif status == 403:
        # Check rate limiting headers
        rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
        if rate_limit_remaining == "0":
            raise GitHubServiceError(
                "GitHub API rate limit exceeded. Please wait a while, or use a custom GitHub "
                "Personal Access Token (PAT) to bypass the limit."
            )
        else:
            raise GitHubServiceError(
                f"GitHub API permission denied (403 Forbidden).{detail} Ensure your {token_type} "
                "has the necessary scopes (e.g. 'repo' for private repositories, or 'actions:read')."
            )

    elif status == 404:
        if run_id is not None:
            raise GitHubServiceError(
                f"Run {run_id} or its logs were not found in '{owner}/{repo}'.{detail} "
                "The run might have been deleted, or your token may lack permissions to view it."
            )
        else:
            raise GitHubServiceError(
                f"Repository '{owner}/{repo}' not found.{detail} Verify the owner and repository names. "
                f"If the repository is private, ensure your {token_type} is configured and has access."
            )

    # General HTTP error fallback
    raise GitHubServiceError(
        f"GitHub API request failed with status code {status}.{detail}"
    )



async def fetch_workflows(owner: str, repo: str, token: str | None = None) -> list[dict]:
    """Fetch all workflows for a GitHub repository."""

    _validate_repo_params(owner, repo)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_build_headers(token))

    if response.status_code != 200:
        _handle_github_error(response, owner, repo, custom_token_used=bool(token))

    response.raise_for_status()
    data = response.json()

    return [
        {
            "id": w["id"],
            "name": w["name"],
            "path": w.get("path", ""),
            "state": w.get("state", "unknown"),
        }
        for w in data.get("workflows", [])
    ]


async def fetch_runs(
    owner: str,
    repo: str,
    *,
    workflow_id: int | None = None,
    status: str | None = None,
    per_page: int = 100,
    token: str | None = None,
) -> list[dict]:
    """Fetch workflow runs, optionally filtered by workflow_id and/or status."""

    _validate_repo_params(owner, repo)

    if workflow_id:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
    else:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs"

    params: dict[str, str | int] = {"per_page": per_page}
    if status:
        params["status"] = status

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_build_headers(token), params=params)

    if response.status_code != 200:
        _handle_github_error(response, owner, repo, custom_token_used=bool(token))

    response.raise_for_status()
    data = response.json()

    return [
        {
            "id": r["id"],
            "name": r.get("name", ""),
            "workflow_name": r.get("name", ""),
            "head_branch": r.get("head_branch", ""),
            "status": r.get("status", ""),
            "conclusion": r.get("conclusion", ""),
            "created_at": r.get("created_at", ""),
            "updated_at": r.get("updated_at", ""),
            "html_url": r.get("html_url", ""),
            "run_number": r.get("run_number", 0),
        }
        for r in data.get("workflow_runs", [])
    ]


async def _fetch_total_count(
    owner: str,
    repo: str,
    *,
    status: str = "completed",
    token: str | None = None,
) -> int:
    """Fetch only the total_count from the GitHub runs API (single lightweight call)."""

    _validate_repo_params(owner, repo)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs"
    params: dict[str, str | int] = {"per_page": 1, "status": status}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_build_headers(token), params=params)

    if response.status_code in (401, 403, 404):
        return 0

    response.raise_for_status()
    return response.json().get("total_count", 0)


async def fetch_failed_runs(
    owner: str,
    repo: str,
    per_page: int = 100,
    token: str | None = None,
) -> dict:
    """Fetch failed runs using GitHub's status=failure filter for stable, consistent results.

    Uses the GitHub API's status=failure parameter directly instead of fetching
    all completed runs and filtering client-side. This prevents fluctuating counts
    on active repos like facebook/react where new runs constantly shift the window.
    """

    # Fetch failed runs directly using GitHub's status=failure filter.
    failed_runs = await fetch_runs(
        owner, repo, status="failure", per_page=per_page, token=token
    )

    # Fetch total completed and failed counts via lightweight API calls (per_page=1, only need total_count).
    total_completed = await _fetch_total_count(owner, repo, status="completed", token=token)
    total_failed = await _fetch_total_count(owner, repo, status="failure", token=token)

    # Use the API's total_count for accurate stats (covers all runs, not just the page).
    total = total_completed if total_completed > 0 else len(failed_runs)
    failed = total_failed if total_failed > 0 else len(failed_runs)
    success_rate = round(((total - failed) / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_runs": total,
        "failed_runs": failed,
        "success_rate": success_rate,
        "runs": failed_runs,
    }


async def download_run_logs(owner: str, repo: str, run_id: int, token: str | None = None) -> str:
    """Download and extract workflow run logs as plain text."""

    _validate_repo_params(owner, repo)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_build_headers(token))

    if response.status_code != 200:
        _handle_github_error(response, owner, repo, custom_token_used=bool(token), run_id=run_id)

    response.raise_for_status()

    # GitHub returns logs as a ZIP archive.
    try:
        log_parts: list[str] = []
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for name in sorted(zf.namelist()):
                if name.endswith(".txt"):
                    content = zf.read(name).decode("utf-8", errors="replace")
                    log_parts.append(f"--- {name} ---\n{content}\n")

        combined = "\n".join(log_parts).strip()
        if not combined:
            raise GitHubServiceError(f"No text log files found in the archive for run {run_id}.")

        return combined

    except zipfile.BadZipFile as exc:
        raise GitHubServiceError(f"GitHub returned an invalid log archive for run {run_id}.") from exc


async def get_run_details(owner: str, repo: str, run_id: int, token: str | None = None) -> dict:
    """Get details for a specific workflow run."""

    _validate_repo_params(owner, repo)

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}"

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, headers=_build_headers(token))

    if response.status_code != 200:
        _handle_github_error(response, owner, repo, custom_token_used=bool(token), run_id=run_id)

    response.raise_for_status()
    r = response.json()

    return {
        "id": r["id"],
        "name": r.get("name", ""),
        "workflow_name": r.get("name", ""),
        "head_branch": r.get("head_branch", ""),
        "status": r.get("status", ""),
        "conclusion": r.get("conclusion", ""),
        "created_at": r.get("created_at", ""),
        "html_url": r.get("html_url", ""),
    }
