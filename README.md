# CDM Company Management Portal

Monorepo containing two implementations of the portal:

- `apps/api` — Express + Prisma API with role-based auth
- `apps/web` — React + Vite frontend
- `cdm_reflex_portal/` — Python + Reflex implementation (SQLite, standalone)

---

## Reflex Portal (Python) — quick start

### Run on Windows
Double-click **`START CDM Portal.bat`** — it handles everything automatically (venv, deps, launch).

Or from a terminal at the repo root:
```bat
run.bat
```

### Run on Linux / Mac
```bash
bash run.sh
```

### Docker
```bash
# Standard run (data persisted)
docker compose up

# Testing mode (fresh ephemeral DB)
docker compose -f docker-compose.yml -f docker-compose.testing.yml up --build
```

**App URLs:** `http://localhost:3000` (frontend) · `http://localhost:8001` (backend)

---

## Node.js Apps (apps/) — quick start

1. Install dependencies:
   ```
   npm install
   ```
2. Create API env from example:
   ```
   copy apps\api\.env.example apps\api\.env
   ```
3. Initialize database:
   ```
   npm run prisma:push -w apps/api
   npm run prisma:seed -w apps/api
   ```
4. Run apps:
   ```
   npm run dev
   ```

Web runs on port 5173, API runs on port 4000.

---

## Features (Reflex portal)

### Companies
- Add, edit, search companies
- Fields: Name, CIN, Class (Public/Private), Registered Address, Notes, Status
- Role-based actions: ADMIN/EDITOR can add/edit, VIEWER is read-only

### Directors Registry
- Separate Directors tab with its own registry
- Fields: DIN (unique), Name, Email, Phone, Status
- Add, edit, search directors

### Company–Director Associations
- Link directors to companies via the **people icon** on any company row
- Each association carries a **Share %** (mandatory, must be > 0)
- Total share across all directors for a company cannot exceed 100%
- A director cannot be added to the same company twice
- Remove associations with inline confirmation prompt

### User Management (ADMIN only)
- Admin tab to create/manage users
- Roles: ADMIN, EDITOR, VIEWER

---

## Stack (Reflex portal)
- Reflex (frontend + backend runtime)
- SQLite + SQLAlchemy
- bcrypt for password hashing

## Notes
- Local SQLite database is stored in `data/cdm.db` (git-ignored).
- For multi-user production, avoid storing a shared live SQLite database in OneDrive sync folders.
  Use OneDrive for backups/exports and migrate primary data to a proper database server or
  Microsoft 365-backed APIs during production rollout.
