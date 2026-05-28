# CDM Company Management Portal

Monorepo containing:
- `apps/api`: Express + Prisma API with role-based auth
- `apps/web`: React + Vite frontend

## Quick start

1. Install dependencies:
   - `npm install`
2. Create API env from example:
   - `copy apps\\api\\.env.example apps\\api\\.env`
3. Initialize database:
   - `npm run prisma:push -w apps/api`
   - `npm run prisma:seed -w apps/api`
4. Run apps:
   - `npm run dev`

Web runs on port 5173, API runs on port 4000.
