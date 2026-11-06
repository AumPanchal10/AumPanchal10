"""Generate self-contained stats cards for the profile README.

Writes assets/stats.svg (GitHub overview) and assets/leetcode.svg (LeetCode progress).
Needs no personal access token: it uses the public GitHub API (with GITHUB_TOKEN when
available, for a higher rate limit) and LeetCode's public GraphQL endpoint.
Standard library only.

Usage:
  python scripts/generate_stats.py               # live data
  python scripts/generate_stats.py --placeholder # write 'not generated yet' cards
  python scripts/generate_stats.py --mock        # sample data, for design previews only
"""
import html
import json
import os
import sys
import urllib.request
from collections import Counter

USER = os.environ.get("GH_USER", "AumPanchal10")
LC_USER = os.environ.get("LEETCODE_USER", "aumpanchal")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("ASSETS_DIR", "assets")

BG, BORDER, TXT, MUTED, LIME = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#84cc16"
FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
LANG_COLORS = ["#84cc16", "#22c55e", "#14b8a6", "#38bdf8", "#a78bfa", "#f59e0b"]


def esc(s):
    return html.escape(str(s), quote=True)


def http_json(url, data=None, headers=None):
    h = {"User-Agent": "profile-stats", "Accept": "application/json"}
    h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    if body:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gh(path):
    headers = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return http_json(f"https://api.github.com{path}", headers=headers)


def frame(w, h, title, body, subtitle=""):
    sub = f'<text x="{w-28}" y="38" text-anchor="end" font-size="13" fill="{MUTED}">{esc(subtitle)}</text>' if subtitle else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}" font-family="{FONT}">
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
  <text x="28" y="38" font-size="18" font-weight="700" fill="{LIME}">{esc(title)}</text>
  {sub}
{body}</svg>
'''


def bar(x, y, w_total, frac, color, delay=0.0):
    w = max(0.0, min(1.0, frac)) * w_total
    return (f'  <rect x="{x}" y="{y}" width="{w_total}" height="10" rx="5" fill="#21262d"/>\n'
            f'  <rect x="{x}" y="{y}" width="{w:.1f}" height="10" rx="5" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" dur="1.1s" begin="{delay}s" fill="freeze"/></rect>\n')


def github_card(d):
    stats = [("Public repos", d["repos"]), ("Stars earned", d["stars"]), ("Followers", d["followers"]), ("Forks", d["forks"])]
    b = ""
    for i, (label, value) in enumerate(stats):
        x = 28 + (i % 2) * 175
        y = 92 + (i // 2) * 70
        b += f'  <text x="{x}" y="{y}" font-size="30" font-weight="700" fill="{TXT}">{esc(value)}</text>\n'
        b += f'  <text x="{x}" y="{y+22}" font-size="13" fill="{MUTED}">{esc(label)}</text>\n'
    b += f'  <text x="410" y="66" font-size="13" font-weight="600" fill="{MUTED}">Top languages (by repository)</text>\n'
    total = sum(c for _, c in d["langs"]) or 1
    for i, (name, count) in enumerate(d["langs"]):
        y = 88 + i * 30
        pct = count / total
        b += f'  <text x="410" y="{y+9}" font-size="13" fill="{TXT}">{esc(name)}</text>\n'
        b += bar(520, y, 190, pct, LANG_COLORS[i % len(LANG_COLORS)], delay=i * 0.12)
        b += f'  <text x="772" y="{y+9}" font-size="13" text-anchor="end" fill="{MUTED}">{pct*100:.0f}%</text>\n'
    return frame(800, 250, "GitHub overview", b, f"@{USER}")


def leetcode_card(d):
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
        b += f'  <text x="300" y="{y+9}" font-size="14" fill="{colors[k]}" font-weight="600">{k}</text>\n'
        b += bar(380, y, 270, frac, colors[k], delay=i * 0.15)
        b += f'  <text x="772" y="{y+9}" font-size="13" text-anchor="end" fill="{MUTED}">{label}</text>\n'
    return frame(800, 190, "LeetCode progress", b, f"@{LC_USER}")


def message_card(title, msg, h=130):
    b = f'  <text x="28" y="84" font-size="14" fill="{MUTED}">{esc(msg)}</text>\n'
    return frame(800, h, title, b)


def collect_github():
    u = gh(f"/users/{USER}")
    repos, page = [], 1
    while page <= 5:
        chunk = gh(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r.get("fork")]
    langs = Counter(r["language"] for r in own if r.get("language"))
    return {
        "repos": u.get("public_repos", len(own)),
        "followers": u.get("followers", 0),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "forks": sum(r.get("forks_count", 0) for r in own),
        "langs": langs.most_common(5),
    }


def collect_leetcode():
    query = ("query($username:String!){allQuestionsCount{difficulty count} "
             "matchedUser(username:$username){submitStats{acSubmissionNum{difficulty count}}}}")
    res = http_json("https://leetcode.com/graphql", {"query": query, "variables": {"username": LC_USER}},
                    {"Referer": "https://leetcode.com", "Origin": "https://leetcode.com"})
    data = res["data"]
    ac = {x["difficulty"]: x["count"] for x in data["matchedUser"]["submitStats"]["acSubmissionNum"]}
    totals = {x["difficulty"]: x["count"] for x in data.get("allQuestionsCount") or []}
    return {"total": ac.get("All", sum(ac.get(k, 0) for k in ("Easy", "Medium", "Hard"))),
            "solved": ac, "totals": totals}


def write(name, svg):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", name)


def main():
    if "--placeholder" in sys.argv:
        msg = "Not generated yet. Run the 'Update stats cards' workflow from the Actions tab."
        write("stats.svg", message_card("GitHub overview", msg))
        write("leetcode.svg", message_card("LeetCode progress", msg))
        return
    if "--mock" in sys.argv:
        write("stats.svg", github_card({"repos": 21, "stars": 8, "followers": 5, "forks": 2,
              "langs": [("TypeScript", 9), ("Java", 5), ("Python", 4), ("JavaScript", 2), ("Dart", 1)]}))
        write("leetcode.svg", leetcode_card({"total": 200, "solved": {"Easy": 90, "Medium": 95, "Hard": 15},
              "totals": {"Easy": 900, "Medium": 1900, "Hard": 850}}))
        return
    write("stats.svg", github_card(collect_github()))  # a failure here fails the job on purpose
    try:
        write("leetcode.svg", leetcode_card(collect_leetcode()))
    except Exception as e:  # keep the previous card instead of breaking the run
        print("LeetCode fetch failed, keeping the existing card:", repr(e))


if __name__ == "__main__":
    main()
