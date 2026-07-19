# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This repo contains **two independent implementations** of the same product (a company/director
registry portal for MCA-style company data). They are not connected and do not share code or a
database.

- `cdm_reflex_portal/` — **The active implementation.** Python + [Reflex](https://reflex.dev),
  SQLite (via SQLAlchemy), single-process app that serves both frontend and backend. Nearly all
  commit history and current work targets this directory.
- `apps/api` + `apps/web` — A parallel Express/Prisma/React implementation (Node workspaces monorepo
  at the repo root `package.json`). It has had no commits since early in the project's history
  (`git log -- apps/` to confirm current state) and should be treated as dormant/reference unless
  the user explicitly asks to work on it.

When a task doesn't specify which implementation, assume `cdm_reflex_portal/`.

## Commands

### Reflex portal (`cdm_reflex_portal/`)

Run locally (Linux/Mac):
```bash
bash run.sh          # creates .venv, installs requirements.txt, runs `python -m reflex run`
```
Windows: `run.bat` or double-click `START CDM Portal.bat`.

Manual run without the helper script:
```bash
python -m reflex run                  # frontend :3000, backend :8001
python -m reflex run --loglevel warning
```

Seed test data (creates `admin` / `editor` / `viewer` test accounts and sample companies):
```bash
python scripts/seed_test_data.py
# SEED_RESET=1 python scripts/seed_test_data.py   # wipe + reseed
```

Docker:
```bash
docker compose up                                                     # persistent SQLite volume
docker compose -f docker-compose.yml -f docker-compose.testing.yml up --build   # ephemeral DB, auto-seeded
```

There is no configured lint/typecheck/test command for this app — Reflex has no test suite in this
repo. Verify changes by running the app and exercising the UI (`bash run.sh`, then visit
`http://localhost:3000`).

The SQLite file lives at `data/cdm.db` (git-ignored, created on first run via `init_db()`).

### Node apps (`apps/api`, `apps/web`) — dormant, verify before assuming still relevant

```bash
npm install
copy apps\api\.env.example apps\api\.env      # create API env (needs JWT_SECRET, DATABASE_URL)
npm run prisma:push -w apps/api
npm run prisma:seed -w apps/api
npm run dev             # runs both api (:4000) and web (:5173) concurrently
npm run dev:api          # apps/api only, tsx watch
npm run dev:web          # apps/web only, vite
npm run build            # tsc build for both workspaces
```

## Architecture — Reflex portal

`cdm_reflex_portal/cdm_reflex_portal.py` is a single ~3600-line module containing the entire app:
one large `rx.State` subclass (`PortalState`) followed by component-building functions, followed by
the `app = rx.App()` / `app.add_page(...)` wiring at the bottom. There is one page (`index`); tabs
("companies", "directors", "admin") are client-side state, not separate routes.

Key structural points to know before editing:

- **All state lives in `PortalState`.** Auth, every form's fields, table data, dropdown/filter UI
  state, and dialog visibility flags are all plain attributes on this one class (grouped by comment
  banners like `# ── Companies ──`, `# ── Directors ──`). There's no per-feature state
  decomposition — when adding a field to a form, add it here alongside the existing
  `form_*` / `edit_form_*` attributes and wire a matching `handle_*_change` setter.
- **Two-hop mutation pattern.** Handlers that write to the DB split into a "prepare" method (e.g.
  `save_company`) that validates input and clears the form, and a `commit_*` method (e.g.
  `commit_save`) that does the actual `SessionLocal()` insert/update and refresh. The prepare method
  `return`s the commit method as an event to chain it. Follow this pattern for new mutations rather
  than doing DB work inline in the first handler.
- **Role-based permission checks are manual and repeated per-handler**, not centralized in a
  decorator: `if self.role not in ("ADMIN", "EDITOR"): ... return`. Roles are `ADMIN`, `EDITOR`,
  `VIEWER`. Admin-only actions (user management, deletes) check `self.role == "ADMIN"` explicitly.
  Component code also gates visibility of buttons/tabs using `rx.cond` on `PortalState.role`.
- **`on_page_load`** (wired via `app.add_page(index, on_load=PortalState.on_page_load)`) runs on
  every page load *and* every WebSocket reconnect — it clears all transient form state so stale
  in-memory state is never resurrected after a reconnect, then reloads companies/directors/users if
  authenticated. Keep this in mind: any new transient form state should be cleared here too (see the
  `_clear_*_form` helper methods called at the top of `on_page_load`).
- **Direct SQLAlchemy session usage in handlers** — no repository/service layer. DB access is
  `with SessionLocal() as session: ...` inline inside state methods, using the models from
  `database.py` (`User`, `Company`, `Director`, `CompanyDirector`).
- **Company–Director associations** (`CompanyDirector` model) enforce a uniqueness constraint (one
  director per company) and a business rule — checked in application code, not DB constraints —
  that total `share_percent` across a company's directors cannot exceed 100%.

`cdm_reflex_portal/database.py` defines the SQLAlchemy models and `init_db()`. `init_db()` also runs
ad-hoc `ALTER TABLE ... ADD COLUMN` migrations on startup for columns added after the initial schema
(there is no migration framework/Alembic — new columns must be added to both the model *and* the
`migrations` list in `init_db()` to apply to existing databases). It also seeds a default `admin`
user with a hardcoded password if none exists.

## Architecture — Node apps (apps/api, apps/web)

- `apps/api`: Express + Prisma (SQLite) + JWT auth. `src/server.ts` defines all routes directly
  (no router modules); `src/auth.ts` has `authenticate`/`authorize(roles[])` middleware and JWT
  signing; `src/config.ts` reads required env vars (`JWT_SECRET` is mandatory, throws at startup if
  missing). Request bodies are validated with `zod` schemas defined inline in `server.ts` next to
  each route. Same three-role model (`ADMIN`/`EDITOR`/`VIEWER`) as the Reflex app but re-implemented
  independently — the two `User` tables and password hashes are unrelated.
- `apps/web`: React + Vite + react-router + TanStack Query, talking to the API via `src/lib/api.ts`.
