"""Shared utilities for GitHub Profile 3.0 scripts (Python 3.11+ stdlib only)."""
from __future__ import annotations

import html
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", str(ROOT_DIR / "assets")))


def esc(value: Any) -> str:
    """Safely escape text for XML/SVG/HTML attributes and body."""
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> Any:
    """Load and parse a UTF-8 JSON file."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def is_valid_http_url(url: str) -> bool:
    """Validate an http(s) or mailto URL."""
    if url.startswith("mailto:"):
        return "@" in url[7:]
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def http_json(
    url: str,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
    retries: int = 3,
    backoff_base: float = 1.5,
) -> Any:
    """Fetch JSON over HTTPS with timeout and exponential backoff retries."""
    req_headers: dict[str, str] = {
        "User-Agent": "AumPanchal10-profile-automation/3.0",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    if body is not None:
        req_headers["Content-Type"] = "application/json"

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            last_err = exc
            # Do not retry 4xx client errors except 429 rate limits
            if 400 <= exc.code < 500 and exc.code != 429:
                raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc

        if attempt < retries - 1:
            time.sleep(backoff_base ** attempt)

    assert last_err is not None
    raise last_err


def github_get(path: str, token: str | None = None) -> Any:
    """Perform a GET request against the GitHub REST API without leaking tokens."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return http_json(f"https://api.github.com{path}", headers=headers)
