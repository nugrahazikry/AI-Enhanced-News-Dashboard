# ── Backend Dockerfile ──────────────────────────────────────────────────────
# Build context: prod_v1/ (project root)
# Run:  docker build -f backend/Dockerfile -t news-backend .
# ────────────────────────────────────────────────────────────────────────────

# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: lean runtime image ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages — no build tools, no pip cache
COPY --from=builder /install /usr/local

# Copy backend source
COPY backend/app.py         ./backend/app.py
COPY backend/scripts/       ./backend/scripts/
COPY backend/data/          ./backend/data/

# Copy frontend templates so Flask (Jinja2) can render them
COPY frontend/templates/    ./frontend/templates/

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "backend/app.py"]
