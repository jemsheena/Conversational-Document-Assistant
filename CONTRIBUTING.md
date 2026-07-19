# Contributing

Thanks for your interest in improving Conversational Document Assistant. This is primarily a personal/portfolio project, but issues and pull requests are welcome.

## Getting Started

1. Fork the repository and clone your fork.
2. Follow the [Quick Start](README.md#quick-start) section of the README to get the app running locally (Docker Compose is the fastest path).
3. Create a branch for your change: `git checkout -b feature/short-description`.

## Development Setup

**Backend:**

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Code Style

- **Backend (Python):** formatted and linted with [Ruff](https://docs.astral.sh/ruff/). Run `ruff check .` and `ruff format .` from `backend/` before committing.
- **Frontend (JS/JSX):** linted with ESLint. Run `npm run lint` from `frontend/` before committing.
- Keep functions small and prefer explicit names over comments explaining unclear code.

## Tests

```bash
cd backend
pytest tests/ -v
```

If you add a new module or fix a bug, please add or update a test where practical. Current coverage is intentionally minimal (see [docs/roadmap.md](docs/roadmap.md)) — new tests are especially welcome.

## Commit Messages

Use short, descriptive commit messages in the imperative mood, e.g. `Fix citation validation for empty source list` rather than `Fixed bug`.

## Pull Requests

- Keep PRs focused on a single change where possible.
- Describe **what** changed and **why** in the PR description — the template will prompt you for this.
- Make sure CI (lint + test) passes before requesting review.
- Update the README or `docs/` if your change affects setup, configuration, or architecture.

## Reporting Bugs / Requesting Features

Please use the issue templates under **Issues → New Issue** — they'll prompt you for the information needed to reproduce a bug or evaluate a feature request.

## Questions

Open a [GitHub Discussion](../../discussions) or an issue — there's no separate mailing list or chat for this project.
