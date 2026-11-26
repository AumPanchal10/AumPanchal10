"""Validate all profile configuration JSON files and referenced local assets.

Usage:
  python scripts/validate_profile.py
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from utils import ASSETS_DIR, CONFIG_DIR, ROOT_DIR, is_valid_http_url, load_json

REQUIRED_CONFIGS = [
    "personal.json",
    "experience.json",
    "projects.json",
    "skills.json",
    "education.json",
    "achievements.json",
    "settings.json",
]

ALLOWED_PROJECT_STATUSES = {"Planning", "In Progress", "Completed", "On Hold"}
ALLOWED_EXP_TYPES = {"professional", "internship", "education", "project"}
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_configs() -> list[str]:
    errors: list[str] = []
    parsed: dict[str, dict] = {}

    for filename in REQUIRED_CONFIGS:
        path = CONFIG_DIR / filename
        if not path.exists():
            errors.append(f"Missing required config file: config/{filename}")
            continue
        try:
            data = load_json(path)
            if not isinstance(data, dict):
                errors.append(f"config/{filename} must have a JSON object at top level")
                continue
            parsed[filename] = data
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in config/{filename}: {exc}")

    if errors:
        return errors

    # 1. Personal
    personal = parsed["personal.json"]
    for key in ("name", "github_username", "headline", "introduction", "links"):
        if not personal.get(key):
            errors.append(f"config/personal.json missing required field '{key}'")
    links = personal.get("links", {})
    if isinstance(links, dict):
        for link_name, link_val in links.items():
            if not link_val:
                continue
            if link_name == "email":
                if "@" not in str(link_val):
                    errors.append(f"config/personal.json invalid email: {link_val}")
            elif not is_valid_http_url(str(link_val)):
                errors.append(f"config/personal.json invalid URL for '{link_name}': {link_val}")

    # 2. Experience
    timeline = parsed["experience.json"].get("timeline")
    if not isinstance(timeline, list) or not timeline:
        errors.append("config/experience.json must contain a non-empty 'timeline' list")
    else:
        seen_exp_ids: set[str] = set()
        for idx, item in enumerate(timeline):
            eid = item.get("id")
            if not eid:
                errors.append(f"config/experience.json timeline[{idx}] missing 'id'")
            elif eid in seen_exp_ids:
                errors.append(f"config/experience.json duplicate id '{eid}'")
            else:
                seen_exp_ids.add(eid)
            if item.get("type") not in ALLOWED_EXP_TYPES:
                errors.append(
                    f"config/experience.json '{eid}' has invalid type '{item.get('type')}' "
                    f"(allowed: {sorted(ALLOWED_EXP_TYPES)})"
                )
            for req in ("role", "organization", "start_date", "end_date"):
                if not item.get(req):
                    errors.append(f"config/experience.json '{eid}' missing '{req}'")

    # 3. Projects
    projects = parsed["projects.json"].get("projects")
    if not isinstance(projects, list) or not projects:
        errors.append("config/projects.json must contain a non-empty 'projects' list")
    else:
        seen_proj_ids: set[str] = set()
        for idx, proj in enumerate(projects):
            pid = proj.get("id")
            if not pid:
                errors.append(f"config/projects.json projects[{idx}] missing 'id'")
            elif pid in seen_proj_ids:
                errors.append(f"config/projects.json duplicate project id '{pid}'")
            else:
                seen_proj_ids.add(pid)
            for req in ("name", "category", "one_liner", "problem", "contribution", "architecture"):
                if not proj.get(req):
                    errors.append(f"config/projects.json '{pid}' missing '{req}'")
            status = proj.get("status")
            if status not in ALLOWED_PROJECT_STATUSES:
                errors.append(
                    f"config/projects.json '{pid}' has invalid status '{status}' "
                    f"(allowed: {sorted(ALLOWED_PROJECT_STATUSES)})"
                )
            preview = proj.get("preview_image")
            if preview:
                preview_path = ROOT_DIR / preview
                if not preview_path.exists():
                    errors.append(f"config/projects.json '{pid}' preview_image not found: {preview}")
            for url_field in ("repo_url", "live_url"):
                url_val = proj.get(url_field)
                if url_val and not is_valid_http_url(str(url_val)):
                    errors.append(f"config/projects.json '{pid}' invalid {url_field}: {url_val}")

    # 4. Skills
    categories = parsed["skills.json"].get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append("config/skills.json must contain a non-empty 'categories' list")

    # 5. Education & Achievements
    if not isinstance(parsed["education.json"].get("education"), list):
        errors.append("config/education.json must contain an 'education' list")
    if not isinstance(parsed["achievements.json"].get("certifications"), list):
        errors.append("config/achievements.json must contain a 'certifications' list")
    if not isinstance(parsed["achievements.json"].get("achievements"), list):
        errors.append("config/achievements.json must contain an 'achievements' list")

    # 6. Settings
    settings = parsed["settings.json"]
    theme = settings.get("theme", {})
    for color_key, color_val in theme.items():
        if not HEX_COLOR_RE.match(str(color_val)):
            errors.append(f"config/settings.json invalid hex color '{color_key}': {color_val}")
    analytics = settings.get("analytics", {})
    if not analytics.get("github_user"):
        errors.append("config/settings.json analytics.github_user is required")

    # 7. Validate all local SVG files parse as well-formed XML
    for svg_path in sorted(ASSETS_DIR.rglob("*.svg")):
        try:
            ET.parse(svg_path)
        except ET.ParseError as exc:
            rel = svg_path.relative_to(ROOT_DIR)
            errors.append(f"Invalid SVG XML in {rel}: {exc}")

    return errors


def main() -> int:
    errors = validate_configs()
    if errors:
        print("Profile validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("Profile validation passed: all configs and SVG assets are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
