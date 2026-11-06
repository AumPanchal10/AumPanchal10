#!/usr/bin/env python3
"""Generate the GitHub profile README from profile.json.

Local edit flow:
  1. Edit profile.json.
  2. Run: python scripts/generate_readme.py

Optional GitHub activity refresh:
  python scripts/generate_readme.py --refresh-github

The script uses only Python's standard library.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "profile.json"
RECENT_PATH = ROOT / ".github" / "recent-repositories.json"
README_PATH = ROOT / "README.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def refresh_recent_repositories(profile: dict[str, Any]) -> list[dict[str, Any]]:
    username = profile["profile"]["username"]
    settings = profile.get("recent_repositories", {})
    excluded = set(settings.get("exclude", [])) | {username}
    limit = int(settings.get("limit", 5))

    url = f"https://api.github.com/users/{username}/repos?sort=updated&direction=desc&per_page=100&type=owner"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        repositories = json.loads(response.read().decode("utf-8"))

    recent: list[dict[str, Any]] = []
    for repo in repositories:
        if repo.get("private") or repo.get("fork") or repo.get("archived"):
            continue
        if repo.get("name") in excluded:
            continue
        recent.append({
            "name": repo.get("name", "Repository"),
            "description": repo.get("description") or "No description added yet.",
            "url": repo.get("html_url", ""),
            "language": repo.get("language") or "Not specified",
            "stars": int(repo.get("stargazers_count") or 0),
            "updated_at": repo.get("updated_at", ""),
        })
        if len(recent) >= limit:
            break

    save_json(RECENT_PATH, recent)
    return recent


def inline_tags(items: list[str]) -> str:
    return " · ".join(f"`{item}`" for item in items)


def render_recent(recent: list[dict[str, Any]]) -> str:
    if not recent:
        return "_No public repository activity is available yet. This section refreshes automatically when the scheduled workflow runs._"
    lines = ["| Repository | Language | Stars | Last updated |", "|---|---:|---:|---:|"]
    for repo in recent:
        name = repo.get("name", "Repository").replace("|", "-")
        description = repo.get("description", "").replace("|", "-").replace("\n", " ")
        url = repo.get("url", "")
        language = repo.get("language", "Not specified")
        updated = repo.get("updated_at", "")
        try:
            updated = datetime.fromisoformat(updated.replace("Z", "+00:00")).strftime("%d %b %Y")
        except (ValueError, AttributeError):
            updated = "—"
        title = f"[{name}]({url})" if url else name
        lines.append(f"| {title}<br><sub>{description}</sub> | {language} | {repo.get('stars', 0)} | {updated} |")
    return "\n".join(lines)


def render(profile: dict[str, Any], recent: list[dict[str, Any]]) -> str:
    person = profile["profile"]
    education = profile["education"]
    generated = datetime.now(timezone.utc).strftime("%d %B %Y")

    out: list[str] = []
    out += [
        "<!--",
        "  AUTO-GENERATED FILE: do not edit README.md directly.",
        "  Edit profile.json, then run: python scripts/generate_readme.py",
        "  GitHub Actions refreshes repository activity every week and on manual dispatch.",
        "-->",
        "",
        f"<h1 align=\"center\">Hi, I'm {person['name']} 👋</h1>",
        "",
        f"<p align=\"center\"><strong>{person['headline']}</strong></p>",
        "",
        "<p align=\"center\">",
        f"  <a href=\"{person['portfolio']}\">Portfolio</a> ·",
        f"  <a href=\"{person['linkedin']}\">LinkedIn</a> ·",
        f"  <a href=\"{person['github']}\">GitHub</a> ·",
        f"  <a href=\"{person['leetcode']}\">LeetCode</a> ·",
        f"  <a href=\"mailto:{person['email']}\">Email</a>",
        "</p>",
        "",
        "<p align=\"center\">",
        f"  <img src=\"https://komarev.com/ghpvc/?username={person['username']}&label=Profile%20views&color=84cc16&style=flat\" alt=\"Profile views\" />",
        "  <img src=\"https://img.shields.io/github/followers/" + person["username"] + "?label=Followers&style=flat&color=84cc16\" alt=\"GitHub followers\" />",
        "</p>",
        "",
        "---",
        "",
        "## About me",
        "",
        person["summary"],
        "",
        f"- 🎓 **Education:** {education['degree']} — {education['institution']} ({education['period']}); CGPA **{education['cgpa']}**.",
        "- 💼 **Current role:** Full-Stack Development Trainee at **LTIMindtree** — Media & Entertainment domain, Paramount client account.",
        "- 🧭 **Project leadership:** Team Lead for SafarMate AI; independently developed Skybooker during LTIMindtree training.",
        "- 🔐 **Interests:** application security, IAM, VAPT, cloud security and full-stack engineering.",
        "",
        "### Current focus",
        "",
    ]
    out.extend(f"- {item}" for item in person.get("current_focus", []))
    out += ["", "## Experience", ""]

    for job in profile.get("experience", []):
        out += [
            f"### {job['role']} · {job['company']}",
            f"_ {job['period']} · {job.get('context', '')} _".replace("_ ", "_").replace(" _", "_"),
            "",
        ]
        out.extend(f"- {item}" for item in job.get("highlights", []))
        if job.get("tags"):
            out += ["", f"**Technologies / focus:** {inline_tags(job['tags'])}"]
        out.append("")

    out += ["## Featured projects", "", "| Project | Overview | Stack | Source |", "|---|---|---|---|"]
    for project in profile.get("projects", []):
        project_name = project["name"]
        url = project.get("url", "")
        project_link = f"[{project_name}]({url})" if url else f"**{project_name}**"
        source = f"[Repository]({url})" if url else project.get("visibility_note", "Link to be added")
        description = project["description"].replace("|", "-")
        stack = inline_tags(project.get("stack", []))
        out.append(f"| {project_link}<br><sub>{project.get('type', '')}</sub> | {description} | {stack} | {source} |")
    out += [
        "",
        "> SafarMate AI and Skybooker are described from the project and resume information currently available. Add their public source URLs to `profile.json` when you publish them.",
        "",
        "## Technical toolkit",
        "",
    ]
    for category, items in profile.get("skills", {}).items():
        out += [f"**{category}**  ", f"{' · '.join(items)}", ""]

    out += ["## Education", "", f"**{education['degree']}** — {education['institution']}  ", f"{education['location']} · {education['period']} · CGPA: **{education['cgpa']}**", ""]
    out += ["## Certifications", ""]
    out.extend(f"- {item}" for item in profile.get("certifications", []))
    out += ["", "## Achievements", ""]
    out.extend(f"- {item}" for item in profile.get("achievements", []))
    out += [
        "",
        "## Recently updated public repositories",
        "",
        "_This section is populated from the GitHub public repositories API and refreshed weekly by GitHub Actions._",
        "",
        render_recent(recent),
        "",
        "## Connect",
        "",
        f"- **Email:** [{person['email']}](mailto:{person['email']})",
        f"- **LinkedIn:** [Aum Panchal]({person['linkedin']})",
        f"- **GitHub:** [@{person['username']}]({person['github']})",
        f"- **Portfolio:** [aumpanchal.netlify.app]({person['portfolio']})",
        f"- **LeetCode:** [aumpanchal]({person['leetcode']})",
        "",
        "---",
        "",
        f"<p align=\"center\"><sub>Made with curiosity · Last generated {generated} · Edit <code>profile.json</code> to keep this profile current.</sub></p>",
        "",
        f"<p align=\"center\">⚡ {person.get('fun_fact', '')}</p>",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Aum Panchal's GitHub profile README")
    parser.add_argument("--refresh-github", action="store_true", help="Fetch latest public repository activity")
    args = parser.parse_args()

    profile = load_json(PROFILE_PATH)
    recent = load_json(RECENT_PATH, []) or []
    if args.refresh_github and profile.get("recent_repositories", {}).get("enabled", True):
        try:
            recent = refresh_recent_repositories(profile)
            print(f"Fetched {len(recent)} public repositories.")
        except Exception as exc:  # Preserve cached activity if GitHub API is temporarily unavailable.
            print(f"Warning: GitHub activity refresh failed; using cached data. Reason: {exc}")

    README_PATH.write_text(render(profile, recent), encoding="utf-8")
    print(f"Generated {README_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
