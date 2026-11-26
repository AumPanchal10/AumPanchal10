"""Deterministically generate README.md from config/*.json inside PROFILE markers.

Preserves existing content outside <!-- PROFILE:START --> / <!-- PROFILE:END --> and
preserves the live <!--RECENT_REPOS:START--> / <!--RECENT_REPOS:END--> block.

Usage:
  python scripts/generate_readme.py
  python scripts/generate_readme.py --check   # exit non-zero if README.md is out of date
"""
from __future__ import annotations

import re
import sys
from typing import Any

from utils import CONFIG_DIR, ROOT_DIR, load_json
from validate_profile import validate_configs

README_PATH = ROOT_DIR / "README.md"
PROFILE_START = "<!-- PROFILE:START -->"
PROFILE_END = "<!-- PROFILE:END -->"
RECENT_START = "<!--RECENT_REPOS:START-->"
RECENT_END = "<!--RECENT_REPOS:END-->"


def _extract_recent_repos_block(readme_text: str) -> str:
    pattern = re.compile(re.escape(RECENT_START) + r"(.*?)" + re.escape(RECENT_END), re.DOTALL)
    match = pattern.search(readme_text)
    if match:
        inner = match.group(1).strip()
        if inner:
            return f"{RECENT_START}\n{inner}\n{RECENT_END}"
    return (
        f"{RECENT_START}\n"
        "- [**PhishNet**](https://github.com/AumPanchal10/PhishNet)\n"
        "- [**CryptoWeather-Nexus**](https://github.com/AumPanchal10/CryptoWeather-Nexus)\n"
        "- [**Totalfit**](https://github.com/AumPanchal10/Totalfit)\n"
        "- [**LeakSense**](https://github.com/AumPanchal10/LeakSense)\n"
        "- [**IndiVerse**](https://github.com/AumPanchal10/IndiVerse)\n"
        f"{RECENT_END}"
    )


def render_profile(recent_repos_block: str) -> str:
    personal: dict[str, Any] = load_json(CONFIG_DIR / "personal.json")
    experience: dict[str, Any] = load_json(CONFIG_DIR / "experience.json")
    projects_data: dict[str, Any] = load_json(CONFIG_DIR / "projects.json")
    skills_data: dict[str, Any] = load_json(CONFIG_DIR / "skills.json")
    education_data: dict[str, Any] = load_json(CONFIG_DIR / "education.json")
    achievements_data: dict[str, Any] = load_json(CONFIG_DIR / "achievements.json")
    settings: dict[str, Any] = load_json(CONFIG_DIR / "settings.json")

    sec = settings.get("sections", {})
    analytics = settings.get("analytics", {})
    gh_user = analytics.get("github_user", personal["github_username"])
    lc_user = analytics.get("leetcode_user", personal.get("leetcode_username", ""))
    links = personal.get("links", {})

    lines: list[str] = []

    # 1. Hero
    if sec.get("hero", True):
        lines.append('<div align="center">')
        lines.append("")
        lines.append(
            f'<p><img src="assets/header.svg" width="100%" alt="{personal["name"]} — {personal["headline"]}"/></p>'
        )
        if personal.get("availability", {}).get("show_indicator"):
            status_text = personal["availability"].get("status_text", "Available")
            lines.append(f'<p><img src="assets/status.svg" width="240" height="38" alt="{status_text}"/></p>')
        lines.append("")

        nav_links: list[str] = []
        if links.get("portfolio"):
            nav_links.append(f"[Portfolio]({links['portfolio']})")
        if links.get("linkedin"):
            nav_links.append(f"[LinkedIn]({links['linkedin']})")
        if links.get("leetcode"):
            nav_links.append(f"[LeetCode]({links['leetcode']})")
        if links.get("email"):
            nav_links.append(f"[Email](mailto:{links['email']})")
        if nav_links:
            lines.append(" · ".join(nav_links))
            lines.append("")

        lines.append(
            "[About](#about) · [Experience](#experience-and-timeline) · [Projects](#featured-projects) · "
            "[Skills](#engineering-skills) · [Analytics](#github-analytics) · [Connect](#connect)"
        )
        lines.append("")
        lines.append("</div>")
        lines.append("")
        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 2. About & At a Glance
    if sec.get("about", True):
        lines.append("## About")
        lines.append("")
        lines.append(personal["introduction"])
        lines.append("")

        glance = personal.get("at_a_glance", [])
        if glance:
            lines.append("| Overview | Details |")
            lines.append("| :--- | :--- |")
            for row in glance:
                lines.append(f"| **{row['label']}** | {row['value']} |")
            lines.append("")

        focus_items = personal.get("current_focus", [])
        if focus_items:
            lines.append("**Current Engineering Focus**")
            lines.append("")
            for item in focus_items:
                lines.append(f"- {item}")
            lines.append("")

        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 3. Experience and Career Timeline
    if sec.get("experience", True):
        lines.append("## Experience and Timeline")
        lines.append("")
        type_labels = {
            "professional": "Full-time",
            "apprenticeship": "Apprenticeship",
            "internship": "Internship",
            "education": "Academic",
            "project": "Project",
        }
        for idx, role in enumerate(experience.get("timeline", [])):
            badge = type_labels.get(role["type"], role["type"].title())
            open_attr = " open" if idx == 0 else ""
            lines.append(f"<details{open_attr}>")
            lines.append(
                f"<summary><b>{role['role']}</b> · {role['organization']} — "
                f"{role['start_date']} – {role['end_date']} ({badge} · {role.get('location', '')})</summary>"
            )
            lines.append("")
            for h in role.get("highlights", []):
                lines.append(f"- {h}")
            techs = role.get("technologies", [])
            if techs:
                lines.append("")
                lines.append(f"**Technologies:** {' · '.join(techs)}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 4. Featured Projects
    if sec.get("projects", True):
        lines.append("## Featured Projects")
        lines.append("")
        lines.append("Select any project below to view its architecture, individual contributions, and implementation details.")
        lines.append("")

        for idx, proj in enumerate(projects_data.get("projects", [])):
            open_attr = " open" if idx == 0 else ""
            lines.append(f"<details{open_attr}>")
            lines.append(
                f"<summary><b>{proj['name']}</b> · {proj['category']} ({proj['status']})</summary>"
            )
            lines.append("")
            lines.append(f"> {proj['one_liner']}")
            lines.append("")
            lines.append(f"- **Problem:** {proj['problem']}")
            lines.append(f"- **Individual Contribution:** {proj['contribution']}")
            lines.append(f"- **Architecture:** {proj['architecture']}")
            lines.append("")
            if proj.get("features"):
                lines.append("**Key Features**")
                lines.append("")
                for feat in proj["features"]:
                    lines.append(f"- {feat}")
                lines.append("")

            if proj.get("preview_image"):
                caption = proj.get("preview_caption") or f"{proj['name']} architecture preview"
                lines.append(f'<p align="center"><img src="{proj["preview_image"]}" width="100%" alt="{caption}"/><br><sub>{caption}</sub></p>')
                lines.append("")

            if proj.get("stack"):
                lines.append(f"**Tech Stack:** {' · '.join(proj['stack'])}")
                lines.append("")

            source_part = f"[Repository]({proj['repo_url']})" if proj.get("repo_url") else proj.get("source_note", "Private repository")
            live_part = f"[Live Demo]({proj['live_url']})" if proj.get("live_url") else "Not deployed"
            health = proj.get("health", {})
            lines.append(
                f"**Source & Health:** {source_part} · **Live:** {live_part} · "
                f"**CI:** {health.get('ci', 'Not configured')} · **Docs:** {health.get('docs', 'N/A')}"
            )
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 5. Engineering Skills
    if sec.get("skills", True):
        lines.append("## Engineering Skills")
        lines.append("")
        for cat in skills_data.get("categories", []):
            lines.append(f"### {cat['title']}")
            lines.append(cat["description"])
            lines.append("")
            lines.append("| Domain | Technologies |")
            lines.append("| :--- | :--- |")
            for grp in cat.get("groups", []):
                items_str = " · ".join(grp["items"])
                lines.append(f"| **{grp['label']}** | {items_str} |")
            lines.append("")

        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 6. Education & Achievements
    if sec.get("education_and_achievements", True):
        lines.append("## Education, Certifications & Achievements")
        lines.append("")
        for edu in education_data.get("education", []):
            lines.append(
                f"- **{edu['degree']}**, {edu['institution']} ({edu['location']}) — "
                f"{edu['start_date']} – {edu['end_date']} · **{edu['grade']}**"
            )
        lines.append("")

        lines.append("<details>")
        lines.append("<summary><b>Certifications & Verified Achievements</b></summary>")
        lines.append("")
        lines.append("**Certifications**")
        for cert in achievements_data.get("certifications", []):
            date_suffix = f" ({cert['date']})" if cert.get("date") else ""
            lines.append(f"- {cert['name']} — {cert['issuer']}{date_suffix}")
        lines.append("")
        lines.append("**Achievements**")
        for ach in achievements_data.get("achievements", []):
            lines.append(f"- {ach}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 7. Currently Building
    if sec.get("currently_building", True) and personal.get("currently_building"):
        lines.append("## Currently Building & Learning")
        lines.append("")
        lines.append("| Initiative | Status | Focus |")
        lines.append("| :--- | :--- | :--- |")
        for item in personal["currently_building"]:
            lines.append(f"| **{item['name']}** | {item['status']} | {item['summary']} |")
        lines.append("")
        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 8. GitHub Analytics Dashboard
    if sec.get("github_analytics", True):
        lines.append("## GitHub Analytics")
        lines.append("")
        if analytics.get("include_snake", True):
            lines.append('<p align="center">')
            lines.append("  <picture>")
            lines.append(
                f'    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{gh_user}/{gh_user}/output/github-snake-dark.svg"/>'
            )
            lines.append(
                f'    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{gh_user}/{gh_user}/output/github-snake.svg"/>'
            )
            lines.append(
                f'    <img alt="Contribution graph snake animation" src="https://raw.githubusercontent.com/{gh_user}/{gh_user}/output/github-snake.svg" width="100%"/>'
            )
            lines.append("  </picture>")
            lines.append("</p>")
            lines.append("")

        lines.append('<p align="center"><img src="assets/stats.svg" alt="GitHub overview stats" width="100%"/></p>')
        lines.append("")
        if (ROOT_DIR / "assets" / "leaderboard.svg").exists():
            lines.append('<p align="center"><img src="assets/leaderboard.svg" alt="Public repository leaderboard" width="100%"/></p>')
            lines.append("")
        if lc_user:
            lc_link = links.get("leetcode", f"https://leetcode.com/u/{lc_user}/")
            lines.append(f'<p align="center"><a href="{lc_link}"><img src="assets/leetcode.svg" alt="LeetCode progress" width="100%"/></a></p>')
            lines.append("")

    if sec.get("recent_repos", True):
        lines.append("### Recently Updated Public Repositories")
        lines.append("")
        lines.append(recent_repos_block)
        lines.append("")
        lines.append('<p align="center"><img src="assets/divider.svg" width="100%" height="20" alt=""/></p>')
        lines.append("")

    # 9. Connect
    if sec.get("connect", True):
        lines.append("## Connect")
        lines.append("")
        if links.get("email"):
            lines.append(f"- **Email:** [{links['email']}](mailto:{links['email']})")
        if links.get("linkedin"):
            lines.append(f"- **LinkedIn:** [{personal['name']}]({links['linkedin']})")
        if links.get("github"):
            lines.append(f"- **GitHub:** [@{gh_user}]({links['github']})")
        if links.get("portfolio"):
            lines.append(f"- **Portfolio:** [{links['portfolio'].replace('https://', '').rstrip('/')}]({links['portfolio']})")
        if links.get("leetcode"):
            lines.append(f"- **LeetCode:** [{lc_user}]({links['leetcode']})")
        lines.append("")
        lines.append('<p align="center"><img src="assets/sine-wave.svg" width="100%" height="100" alt="Animated sine wave"/></p>')
        lines.append("")
        if personal.get("footer_quote"):
            lines.append(f'<p align="center"><i>{personal["footer_quote"]}</i></p>')

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    errors = validate_configs()
    if errors:
        print("Cannot generate README.md due to validation errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    existing = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    recent_block = _extract_recent_repos_block(existing)
    generated_body = render_profile(recent_block)
    new_section = f"{PROFILE_START}\n{generated_body}{PROFILE_END}"

    marker_pattern = re.compile(re.escape(PROFILE_START) + r".*?" + re.escape(PROFILE_END), re.DOTALL)
    if marker_pattern.search(existing):
        updated = marker_pattern.sub(lambda _: new_section, existing)
    else:
        header_comment = (
            "<!--\n"
            "  Generated automatically from config/*.json via `python scripts/generate_readme.py`.\n"
            "  Edit JSON files under config/ instead of editing inside the PROFILE markers.\n"
            "-->\n\n"
        )
        updated = f"{header_comment}{new_section}\n"

    if "--check" in sys.argv:
        if updated != existing:
            print("README.md is out of date. Run `python scripts/generate_readme.py`.", file=sys.stderr)
            return 1
        print("README.md is up to date.")
        return 0

    if updated != existing:
        README_PATH.write_text(updated, encoding="utf-8")
        print("Updated README.md")
    else:
        print("README.md already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
