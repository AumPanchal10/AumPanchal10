# Keep your GitHub profile up to date

This repository uses `profile.json` as the single source of truth. The visible profile page is generated into `README.md`.

## One-time setup

1. Copy `README.md`, `profile.json`, `scripts/`, `.github/` and this guide into the root of `AumPanchal10/AumPanchal10`.
2. Commit and push the files to the `main` branch.
3. In GitHub, open **Settings → Actions → General → Workflow permissions** and allow **Read and write permissions**. This is required so the scheduled workflow can commit the generated README.
4. Open **Actions → Refresh GitHub profile README → Run workflow** once to test it.

## Routine updates (the only file you normally need to edit)

Open `profile.json` and change the relevant values:

- **New job or role:** add/edit an item in `experience`. Put the current role first. Update title, company, dates, client/domain context, highlights and tags.
- **Promotion or client change at LTIMindtree:** edit the LTIMindtree item; do not add a second entry unless it is a genuinely separate role.
- **New project:** add an item to `projects` with a short factual description, stack and public GitHub URL. If it is private, leave `url` empty and set a short `visibility_note`.
- **New technology:** add it to the correct list under `skills`.
- **New certification or achievement:** append it to `certifications` or `achievements`.
- **Contact/profile changes:** edit `profile` (email, LinkedIn, portfolio, summary, focus).

After committing `profile.json`, the workflow generates and commits `README.md` automatically.

## Manual local update

You need Python 3.10+; no extra packages are required.

```bash
python scripts/generate_readme.py
```

To also refresh the recent public repositories cache from GitHub:

```bash
python scripts/generate_readme.py --refresh-github
```

Then commit the generated files:

```bash
git add profile.json README.md .github/recent-repositories.json
git commit -m "Update GitHub profile"
git push
```

## What updates automatically?

- The `Recently updated public repositories` table is refreshed every Monday at 03:30 UTC and when the workflow is run manually.
- The generated date is refreshed whenever the workflow runs.
- GitHub's profile contribution graph, repository stars and follower count remain managed by GitHub itself. The follower/profile-view badges in the README are external badge services and can occasionally be unavailable.

## What does not update automatically?

A public GitHub API cannot reliably infer your employment title, client assignment, responsibilities, private projects, certification completions or resume changes. Update those facts in `profile.json` when they change. The scheduled workflow then republishes the README using the latest saved information.

## Accuracy checks before publishing

- Confirm job titles, employment dates and client/account wording against your HR records or current resume.
- Do not include confidential client information, internal system names, customer data, credentials or proprietary code details.
- Only add measurable impact when you can substantiate it.
- Keep private projects private; do not expose private repository URLs or internal details.
