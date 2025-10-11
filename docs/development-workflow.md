# Contributor Workflow Guide

Quick reference for contributors.

## 1. Get Oriented
- Read `README.md` for the product snapshot and stack overview.
- Scan `docs/development.md` for local setup, conventions, and directory responsibilities.
- Review `docs/data-model.md` to understand the proposed database schema.
- Check `docs/wslconfig.md` (Windows only) if Docker/WSL memory usage is an issue.

## 2. Sync Your Local Environment
1. Ensure you are on the `main` branch:
	```bash
	git checkout main
	```
2. Pull the latest changes and remote refs:
	```bash
	git fetch --all
	git pull --rebase origin main
	```
3. Start Docker Desktop (WSL2 backend on Windows) and make sure your `.env` is up to date (`infra/.env`).
4. Rebuild/restart containers if dependencies changed:
	```bash
	cd infra
	docker compose up -d --build
	```

## 3. Create a Feature Branch
1. From the repository root:
	```bash
	git checkout -b feature/<short-description>
	```
2. Keep the branch focused on one task. Rebase against `main` if it falls behind:
	```bash
	git fetch --all
	git rebase origin/main
	```

## 4. Make Changes in the Right Place
- **Backend** (`backend/app/`):
  - Routes in `api/routes/`, services in `services/`, repositories in `repositories/`, schemas in `schemas/`.
  - Update `backend/tests/` with integration or unit coverage for new behaviour.
- **Frontend** (`frontend/`): static assets live in `public/`. If you add tooling, document it in `frontend/README.md` and use `src/` for new source files.
- **Infrastructure** (`infra/`): store Docker, Compose, env templates, and deployment scripts here. Explain non-obvious tweaks in comments or `infra/README.md`.
- **Documentation** (`docs/`): add or update markdown guides when behaviour or setup changes. New directories should receive a concise `README.md`.
- **Scripts** (`scripts/`): helper automation (seeding, linting) belongs here; include usage instructions in `scripts/README.md`.

## 5. Test & Validate
- Run backend tests before committing:
  ```bash
  docker compose exec swampninjas pytest
  ```
- Manually verify endpoints or UI changes when applicable (e.g., `http://localhost:8000/`).
- When adjusting infrastructure, document reproduction steps and verify containers restart cleanly.

## 6. Commit Thoughtfully
1. Check your worktree:
	```bash
	git status
	```
2. Stage and commit with descriptive messages (Australian English, present tense):
	```bash
	git add <files>
	git commit -m "Add question repository skeleton"
	```
3. Keep commits small and logical; update docs in the same commit when feasible.

## 7. Push & Open a Pull Request
1. Push your branch:
	```bash
	git push -u origin feature/<short-description>
	```
2. Open a PR on GitHub summarising:
	- What changed and why.
	- How it was tested (commands run, screenshots, etc.).
	- Any follow-up tasks or known limitations.

## 8. Collaborate & Follow Up
- Share progress or blockers in the project Discord channel.
- After merging, switch back to `main`, pull the latest changes, and delete the feature branch locally and on origin.
