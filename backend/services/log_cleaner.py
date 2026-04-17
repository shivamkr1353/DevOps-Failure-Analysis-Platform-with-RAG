import re


RELEVANT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\berror\b",
        r"\bfailed\b",
        r"\bfailure\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\btimeout\b",
        r"\bdenied\b",
        r"module not found",
        r"no module named",
        r"could not",
        r"cannot",
        r"non-zero code",
        r"returned exit code",
    )
]

NOISE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^\s*$",
        r"^\s*remote:\s+counting objects",
        r"^\s*remote:\s+compressing objects",
        r"^\s*receiving objects",
        r"^\s*resolving deltas",
        r"^\s*already up to date\.*\s*$",
        r"^\s*##\[[a-z]+\]",
        r"^\s*=+\s*$",
        r"^\s*-+\s*$",
    )
]

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi_codes(text: str) -> str:
    """Remove terminal color codes that add noise to CI logs."""

    return ANSI_ESCAPE_PATTERN.sub("", text)


def is_noise_line(line: str) -> bool:
    """Return True for obviously low-signal log lines."""

    return any(pattern.search(line) for pattern in NOISE_PATTERNS)


def is_relevant_line(line: str) -> bool:
    """Return True for lines that look related to the actual failure."""

    return any(pattern.search(line) for pattern in RELEVANT_PATTERNS)


def extract_focus_lines(lines: list[str], context_window: int = 2) -> list[str]:
    """Keep relevant lines and a small amount of context around them."""

    relevant_indexes: set[int] = set()

    for index, line in enumerate(lines):
        if is_relevant_line(line):
            start = max(0, index - context_window)
            end = min(len(lines), index + context_window + 1)
            relevant_indexes.update(range(start, end))

    if not relevant_indexes:
        compacted_lines = [line for line in lines if not is_noise_line(line)]
        return compacted_lines[:80]

    return [lines[index] for index in sorted(relevant_indexes) if not is_noise_line(lines[index])]


def clean_logs(logs: str) -> str:
    """Preprocess logs before sending them to the LLM."""

    sanitized_logs = strip_ansi_codes(logs.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.rstrip() for line in sanitized_logs.split("\n")]
    focus_lines = extract_focus_lines(lines)

    # Fall back to raw lines if cleaning removes everything.
    final_lines = focus_lines or [line for line in lines if line.strip()]
    return "\n".join(final_lines[:120]).strip()

