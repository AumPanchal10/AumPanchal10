"""Refresh the 'Recently updated repositories' block in README.md.

Replaces everything between the RECENT_REPOS markers with the user's most
recently pushed public, non-fork repositories (profile repo excluded).
Uses only the standard library.
"""
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "AumPanchal10")
TOKEN = os.environ.get("GITHUB_TOKEN")
LIMIT = 5
README = "README.md"
START, END = "<!--RECENT_REPOS:START-->", "<!--RECENT_REPOS:END-->"


def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?sort=pushed&direction=desc&per_page=50&type=owner"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "readme-refresh"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def render(repos):
    rows = []
    for r in repos:
        if r.get("fork") or r.get("archived") or r["name"].lower() == USER.lower():
            continue
        desc = (r.get("description") or "No description yet").strip()
        lang = f" · `{r['language']}`" if r.get("language") else ""
        stars = f" · ⭐ {r['stargazers_count']}" if r.get("stargazers_count") else ""
        rows.append(
            f"- [**{r['name']}**]({r['html_url']}) — {desc}{lang}{stars} · updated {r['pushed_at'][:10]}"
        )
        if len(rows) == LIMIT:
            break
    return "\n".join(rows) or "_No public repository activity yet._"


def main():
    block = render(fetch_repos())
    text = open(README, encoding="utf-8").read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit("Markers not found in README.md")
    new = pattern.sub(f"{START}\n{block}\n{END}", text)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
