# Stage 1 — build frontend
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — Python runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY --from=frontend /build/dist frontend/dist/

# Data directory — mutable files (db, network config) live here.
# Mount a named volume at /data to persist across container restarts.
RUN mkdir -p /data && \
    echo '{"allowlist":[],"denylist":[],"tool_denylist":[]}' > /data/network_config.json && \
    printf 'agent_type: general\nenvironment: dev\nrole: user\ntenant_id: null\n' > /data/agent_config.yaml

ENV HF_HOME=/cache/huggingface
ENV AEGIS_DATA_DIR=/data
ENV DATABASE_URL=sqlite:////data/aegis.db
ENV AEGIS_AGENT_CONFIG_PATH=/data/agent_config.yaml
ENV PYTHONUNBUFFERED=1

EXPOSE 8765

CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8765"]
