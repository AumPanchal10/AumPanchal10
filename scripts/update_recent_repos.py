"""Refresh the 'Recently updated public repositories' block in README.md.

Replaces everything between <!--RECENT_REPOS:START--> and <!--RECENT_REPOS:END-->
with the user's most recently pushed public, non-fork, non-archived repositories.
Standard library only (Python 3.11+).
"""
from __future__ import annotations

import os
import re
from typing import Any

from utils import CONFIG_DIR, ROOT_DIR, github_get, load_json

SETTINGS: dict[str, Any] = load_json(CONFIG_DIR / "settings.json") if (CONFIG_DIR / "settings.json").exists() else {}
ANALYTICS: dict[str, Any] = SETTINGS.get("analytics", {})

USER = os.environ.get("GH_USER", ANALYTICS.get("github_user", "AumPanchal10"))
TOKEN = os.environ.get("GITHUB_TOKEN")
LIMIT = int(ANALYTICS.get("recent_repos_limit", 5))
EXCLUDE_REPOS = {r.lower() for r in ANALYTICS.get("exclude_repos", [USER])}
README = ROOT_DIR / "README.md"
START, END = "<!--RECENT_REPOS:START-->", "<!--RECENT_REPOS:END-->"


def fetch_repos() -> list[dict[str, Any]]:
    return github_get(
        f"/users/{USER}/repos?sort=pushed&direction=desc&per_page=50&type=owner",
        TOKEN,
    )


def render(repos: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for repo in repos:
        if repo.get("fork") or repo.get("archived") or repo["name"].lower() in EXCLUDE_REPOS:
            continue
        desc = (repo.get("description") or "No description yet").strip()
        lang = f" · {repo['language']}" if repo.get("language") else ""
        stars = f" · ★ {repo['stargazers_count']}" if repo.get("stargazers_count") else ""
        pushed = (repo.get("pushed_at") or "")[:10]
        rows.append(
            f"- [**{repo['name']}**]({repo['html_url']}) — {desc}{lang}{stars} · updated {pushed}"
        )
        if len(rows) == LIMIT:
            break
    return "\n".join(rows) or "_No public repository activity yet._"


def main() -> int:
    block = render(fetch_repos())
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit("RECENT_REPOS markers not found in README.md")
    new_text = pattern.sub(lambda _: f"{START}\n{block}\n{END}", text)
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README updated")
    else:
        print("No changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
