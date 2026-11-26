# GitHub Profile 3.0 — Maintenance & Automation Guide

This repository uses a configuration-driven Python generation system (Python 3.11+ standard library only) alongside a lightweight Node.js local preview server.

## Directory Structure

- `config/` — Structured JSON profile data (`personal.json`, `experience.json`, `projects.json`, `skills.json`, `education.json`, `achievements.json`, `settings.json`)
- `scripts/` — Validation, README rendering, analytics SVG generation, and recent-repos updater
- `assets/` — Profile banner, status badge, dividers, analytics cards (`stats.svg`, `leaderboard.svg`, `leetcode.svg`), and project architecture previews (`assets/projects/*`)
- `.github/workflows/` — Automated GitHub Actions (`profile-update.yml`, `stats-update.yml`, `snake.yml`, `validate.yml`)
- `server.ts` — Local Express preview server rendering `README.md` and `/assets` on port `3000`

## Editing Profile Content

1. Update the relevant JSON file inside `config/`.
2. Validate configuration and SVG assets:
   ```bash
   python3 scripts/validate_profile.py
   ```
3. Regenerate `README.md` (only updates content inside `<!-- PROFILE:START --> ... <!-- PROFILE:END -->`):
   ```bash
   python3 scripts/generate_readme.py
   ```
4. Refresh SVG analytics cards or recent repositories locally (optional):
   ```bash
   python3 scripts/generate_stats.py
   python3 scripts/update_recent_repos.py
   ```

## GitHub Actions Workflows

- `profile-update.yml` — Runs weekly (Monday 03:00 UTC), on `config/**` pushes to `main`, or manually via `workflow_dispatch`. Validates config, regenerates `README.md`, refreshes `<!--RECENT_REPOS-->`, and commits only when changed.
- `stats-update.yml` — Sole owner of `assets/stats.svg`, `assets/leaderboard.svg`, and `assets/leetcode.svg` (eliminating previous overlap). Uses `GITHUB_TOKEN` (no extra PAT required).
- `snake.yml` — Generates `github-snake.svg` and `github-snake-dark.svg` on the `output` branch.
- `validate.yml` — Runs Python syntax checks, config validation, SVG XML checks, and `generate_readme.py --check` on pushes and PRs.

## Local Preview Server

Start the local GitHub Profile preview server on `http://localhost:3000`:

```bash
npm install
npm run dev
```
