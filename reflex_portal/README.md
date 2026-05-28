# CDM Portal (Reflex Edition)

This is a Python + Reflex implementation of the company management portal.

## Stack
- Reflex (frontend + backend runtime)
- SQLite + SQLAlchemy
- bcrypt for password hashing

## Features implemented
- Username/password login
- Role model: ADMIN, EDITOR, VIEWER
- Add and edit company records (ADMIN/EDITOR)
- Search companies by CIN or company name
- Responsive portal layout
- Local SQLite persistence (`data/cdm.db`)

## Default login
- Username: `admin`
- Password: `admin123`

## Run (Windows)
1. Open terminal in this folder:
   - `cd reflex_portal`
2. Start app:
   - `run.bat`

## Run (Linux/Mac)
1. Open terminal in this folder:
   - `cd reflex_portal`
2. Start app:
   - `bash run.sh`

## App URLs
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8001`

## Notes on OneDrive transition
For multi-user production, avoid storing a shared live SQLite database directly in OneDrive sync folders. Use OneDrive for backups/exports and move primary multi-user data to Microsoft 365-backed APIs (Graph/SharePoint) during migration.
