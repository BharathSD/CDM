# ── Stage: runtime ────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies (Node.js 20 required by Reflex to build the frontend) ─
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies (cached separately from source) ───────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ─────────────────────────────────────────────────────────
COPY . .

# ── Pre-initialise Reflex (downloads Next.js packages once at build time) ─────
# Suppresses the "do you want to create a new app?" prompt by checking the
# existing rxconfig.py, then installs npm dependencies into .web/
RUN python -m reflex init

# ── Ports: 3000 = Next.js frontend  │  8001 = FastAPI / WebSocket backend ─────
EXPOSE 3000 8001

COPY entrypoint.sh /entrypoint.sh
# Strip Windows CRLF line endings (safe no-op on Linux-authored files too)
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
