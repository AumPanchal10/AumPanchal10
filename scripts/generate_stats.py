"""Generate self-contained SVG analytics cards for the profile README.

Writes:
  - assets/stats.svg        (GitHub account overview & repo language distribution)
  - assets/leaderboard.svg  (Top eligible public repositories excluding profile repo)
  - assets/leetcode.svg     (LeetCode solved progress with graceful fallback)

Standard library only (Python 3.11+).
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from utils import ASSETS_DIR, CONFIG_DIR, esc, github_get, http_json, load_json

SETTINGS: dict[str, Any] = load_json(CONFIG_DIR / "settings.json") if (CONFIG_DIR / "settings.json").exists() else {}
THEME: dict[str, str] = SETTINGS.get("theme", {})
ANALYTICS: dict[str, Any] = SETTINGS.get("analytics", {})

USER = os.environ.get("GH_USER", ANALYTICS.get("github_user", "AumPanchal10"))
LC_USER = os.environ.get("LEETCODE_USER", ANALYTICS.get("leetcode_user", "aumpanchal"))
TOKEN = os.environ.get("GITHUB_TOKEN")
EXCLUDE_REPOS = {r.lower() for r in ANALYTICS.get("exclude_repos", [USER])}

BG = THEME.get("background", "#0D1117")
SURFACE = THEME.get("surface", "#161B22")
BORDER = THEME.get("border", "#30363D")
TXT = THEME.get("primary_text", "#E6EDF3")
MUTED = THEME.get("secondary_text", "#8B949E")
LIME = THEME.get("accent", "#84CC16")
FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
LANG_COLORS = ["#84cc16", "#22c55e", "#14b8a6", "#38bdf8", "#a78bfa", "#f59e0b"]


def frame(w: int, h: int, title: str, body: str, subtitle: str = "") -> str:
    sub = (
        f'<text x="{w - 28}" y="38" text-anchor="end" font-size="13" fill="{MUTED}">{esc(subtitle)}</text>'
        if subtitle
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{esc(title)}" font-family="{FONT}">\n'
        f"  <title>{esc(title)}</title>\n"
        f'  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>\n'
        f'  <text x="28" y="38" font-size="18" font-weight="700" fill="{LIME}">{esc(title)}</text>\n'
        f"  {sub}\n"
        f"{body}</svg>\n"
    )


def bar(x: int, y: int, w_total: int, frac: float, color: str, delay: float = 0.0) -> str:
    w = max(0.0, min(1.0, frac)) * w_total
    return (
        f'  <rect x="{x}" y="{y}" width="{w_total}" height="10" rx="5" fill="#21262d"/>\n'
        f'  <rect x="{x}" y="{y}" width="{w:.1f}" height="10" rx="5" fill="{color}">'
        f'<animate attributeName="width" from="0" to="{w:.1f}" dur="1.0s" begin="{delay:.2f}s" fill="freeze"/></rect>\n'
    )


def github_card(d: dict[str, Any]) -> str:
    stats = [
        ("Public repos", d["repos"]),
        ("Owned stars", d["stars"]),
        ("Followers", d["followers"]),
        ("Owned forks", d["forks"]),
    ]
    b = ""
    for i, (label, value) in enumerate(stats):
        x = 28 + (i % 2) * 175
        y = 92 + (i // 2) * 70
        b += f'  <text x="{x}" y="{y}" font-size="30" font-weight="700" fill="{TXT}">{esc(value)}</text>\n'
        b += f'  <text x="{x}" y="{y + 22}" font-size="13" fill="{MUTED}">{esc(label)}</text>\n'
    b += f'  <text x="410" y="66" font-size="13" font-weight="600" fill="{MUTED}">Top languages (by non-fork repo count)</text>\n'
    total = sum(c for _, c in d["langs"]) or 1
    for i, (name, count) in enumerate(d["langs"]):
        y = 88 + i * 30
        pct = count / total
        b += f'  <text x="410" y="{y + 9}" font-size="13" fill="{TXT}">{esc(name)}</text>\n'
        b += bar(520, y, 190, pct, LANG_COLORS[i % len(LANG_COLORS)], delay=i * 0.1)
        b += f'  <text x="772" y="{y + 9}" font-size="13" text-anchor="end" fill="{MUTED}">{pct * 100:.0f}%</text>\n'
    stamp = d.get("updated_at", "")
    sub = f"@{USER} · {stamp}" if stamp else f"@{USER}"
    return frame(800, 250, "GitHub Overview (Public Scope)", b, sub)


def leaderboard_card(repos: list[dict[str, Any]], updated_at: str = "") -> str:
    limit = int(ANALYTICS.get("leaderboard_limit", 5))
    top = repos[:limit]
    row_h = 34
    h = 76 + max(1, len(top)) * row_h + 16
    b = f'  <line x1="28" y1="54" x2="772" y2="54" stroke="{BORDER}"/>\n'
    if not top:
        b += f'  <text x="28" y="96" font-size="14" fill="{MUTED}">No eligible public repositories found.</text>\n'
    for i, repo in enumerate(top):
        y = 84 + i * row_h
        name = repo["name"]
        lang = repo.get("language") or "Multi"
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        pushed = (repo.get("pushed_at") or "")[:10]
        b += f'  <rect x="28" y="{y - 20}" width="744" height="28" rx="6" fill="{SURFACE}"/>\n'
        b += f'  <text x="40" y="{y - 2}" font-size="13" font-weight="700" fill="{TXT}">{esc(name)}</text>\n'
        b += f'  <text x="310" y="{y - 2}" font-size="12" fill="{LIME}">{esc(lang)}</text>\n'
        b += f'  <text x="470" y="{y - 2}" font-size="12" fill="{MUTED}">Stars: {esc(stars)} · Forks: {esc(forks)}</text>\n'
        b += f'  <text x="758" y="{y - 2}" text-anchor="end" font-size="12" fill="{MUTED}">Updated {esc(pushed)}</text>\n'
    sub = f"Public non-fork repos · {updated_at}" if updated_at else "Public non-fork repos"
    return frame(800, h, "Repository Leaderboard", b, sub)


def leetcode_card(d: dict[str, Any]) -> str:
    b = f'  <text x="28" y="108" font-size="52" font-weight="700" fill="{TXT}">{esc(d["total"])}</text>\n'
    b += f'  <text x="28" y="136" font-size="14" fill="{MUTED}">problems solved</text>\n'
    colors = {"Easy": "#00b8a3", "Medium": "#ffc01e", "Hard": "#ef4743"}
    mx = max([d["solved"].get(k, 0) for k in colors] + [1])
    for i, k in enumerate(["Easy", "Medium", "Hard"]):
        y = 74 + i * 38
        solved = d["solved"].get(k, 0)
        tot = d["totals"].get(k)
        frac = solved / tot if tot else solved / mx
        label = f"{solved} / {tot}" if tot else f"{solved}"
        b += f'  <text x="300" y="{y + 9}" font-size="14" fill="{colors[k]}" font-weight="600">{k}</text>\n'
        b += bar(380, y, 270, frac, colors[k], delay=i * 0.15)
        b += f'  <text x="772" y="{y + 9}" font-size="13" text-anchor="end" fill="{MUTED}">{esc(label)}</text>\n'
    return frame(800, 190, "LeetCode Progress", b, f"@{LC_USER}")


def message_card(title: str, msg: str, h: int = 130) -> str:
    b = f'  <text x="28" y="84" font-size="14" fill="{MUTED}">{esc(msg)}</text>\n'
    return frame(800, h, title, b)


def collect_github() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    u = github_get(f"/users/{USER}", TOKEN)
    repos: list[dict[str, Any]] = []
    page = 1
    while page <= 5:
        chunk = github_get(f"/users/{USER}/repos?per_page=100&type=owner&page={page}", TOKEN)
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r.get("fork") and not r.get("archived")]
    eligible = [r for r in own if r["name"].lower() not in EXCLUDE_REPOS]
    eligible.sort(key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at", "")), reverse=True)
    langs = Counter(r["language"] for r in own if r.get("language"))
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    overview = {
        "repos": u.get("public_repos", len(own)),
        "followers": u.get("followers", 0),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "forks": sum(r.get("forks_count", 0) for r in own),
        "langs": langs.most_common(5),
        "updated_at": today,
    }
    return overview, eligible


def collect_leetcode() -> dict[str, Any]:
    query = (
        "query($username:String!){allQuestionsCount{difficulty count} "
        "matchedUser(username:$username){submitStats{acSubmissionNum{difficulty count}}}}"
    )
    res = http_json(
        "https://leetcode.com/graphql",
        {"query": query, "variables": {"username": LC_USER}},
        {"Referer": "https://leetcode.com", "Origin": "https://leetcode.com"},
    )
    data = res["data"]
    ac = {x["difficulty"]: x["count"] for x in data["matchedUser"]["submitStats"]["acSubmissionNum"]}
    totals = {x["difficulty"]: x["count"] for x in data.get("allQuestionsCount") or []}
    return {
        "total": ac.get("All", sum(ac.get(k, 0) for k in ("Easy", "Medium", "Hard"))),
        "solved": ac,
        "totals": totals,
    }


def write_svg(name: str, svg: str) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    target: Path = ASSETS_DIR / name
    existing = target.read_text(encoding="utf-8") if target.exists() else None
    if existing != svg:
        target.write_text(svg, encoding="utf-8")
        print("wrote", name)
    else:
        print("unchanged", name)


def build_offline_leaderboard_from_projects() -> list[dict[str, Any]]:
    """Build deterministic leaderboard rows from public repos listed in config/projects.json."""
    proj_file = CONFIG_DIR / "projects.json"
    if not proj_file.exists():
        return []
    projects = load_json(proj_file).get("projects", [])
    rows: list[dict[str, Any]] = []
    for proj in projects:
        if proj.get("repo_url"):
            rows.append(
                {
                    "name": proj["name"],
                    "language": proj["stack"][0] if proj.get("stack") else "Project",
                    "stargazers_count": "-",
                    "forks_count": "-",
                    "pushed_at": "Public",
                }
            )
    return rows


def main() -> int:
    if "--placeholder" in sys.argv:
        msg = "Not generated yet. Run the 'Update stats cards' workflow from the Actions tab."
        write_svg("stats.svg", message_card("GitHub Overview (Public Scope)", msg))
        write_svg("leetcode.svg", message_card("LeetCode Progress", msg))
        write_svg("leaderboard.svg", message_card("Repository Leaderboard", msg))
        return 0

    if "--mock" in sys.argv:
        write_svg(
            "stats.svg",
            github_card(
                {
                    "repos": 19,
                    "stars": 1,
                    "followers": 5,
                    "forks": 0,
                    "langs": [("Java", 3), ("TypeScript", 3), ("Python", 2), ("HTML", 2), ("CSS", 1)],
                    "updated_at": "preview",
                }
            ),
        )
        write_svg(
            "leetcode.svg",
            leetcode_card(
                {
                    "total": 190,
                    "solved": {"Easy": 61, "Medium": 111, "Hard": 18},
                    "totals": {"Easy": 975, "Medium": 2139, "Hard": 987},
                }
            ),
        )
        write_svg("leaderboard.svg", leaderboard_card(build_offline_leaderboard_from_projects(), "preview"))
        return 0

    try:
        overview, eligible = collect_github()
        write_svg("stats.svg", github_card(overview))
        write_svg("leaderboard.svg", leaderboard_card(eligible, overview["updated_at"]))
    except Exception as exc:
        print("GitHub fetch failed, keeping existing cards:", repr(exc), file=sys.stderr)
        if not (ASSETS_DIR / "leaderboard.svg").exists():
            write_svg("leaderboard.svg", leaderboard_card(build_offline_leaderboard_from_projects(), "configured"))
        if "--strict" in sys.argv:
            return 1

    try:
        write_svg("leetcode.svg", leetcode_card(collect_leetcode()))
    except Exception as exc:
        print("LeetCode fetch failed, keeping existing card:", repr(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
