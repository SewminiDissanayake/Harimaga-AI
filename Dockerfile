# HariMaga AI: one container with the Flask API + the built React UI.
#
# Build and run locally:
#   docker build -t harimaga .
#   docker run -p 8000:8000 harimaga
# then open http://localhost:8000

# ---- Stage 1: build the React frontend ----
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend that also serves the built frontend ----
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HARIMAGA_BEHIND_PROXY=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /app/frontend/dist ./frontend/dist

# Run as a normal user, not root
RUN useradd --create-home harimaga && chown -R harimaga /app
USER harimaga

EXPOSE 8000
# 1 worker so the in-memory rate limiter and SQLite stay consistent; 4 threads for speed.
CMD gunicorn --chdir webapp/backend app:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 60
