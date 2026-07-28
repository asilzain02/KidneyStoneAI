# ──────────────────────────────────────────────────────────────
# Dockerfile — KidneyStoneAI: Python AI Engine
# Multi-stage build: dependency install + runtime.
# ──────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base
WORKDIR /app

# Install system packages required for OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 1: Install Dependencies ─────────────────────────────
FROM base AS dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM dependencies AS runtime

# Security: non-root user
RUN groupadd -r aiuser && useradd -r -g aiuser aiuser

COPY --chown=aiuser:aiuser api/      ./api/
COPY --chown=aiuser:aiuser prediction/ ./prediction/
COPY --chown=aiuser:aiuser preprocessing/ ./preprocessing/
COPY --chown=aiuser:aiuser postprocessing/ ./postprocessing/
COPY --chown=aiuser:aiuser segmentation/ ./segmentation/
COPY --chown=aiuser:aiuser gradcam/ ./gradcam/
COPY --chown=aiuser:aiuser severity/ ./severity/
COPY --chown=aiuser:aiuser treatment/ ./treatment/
COPY --chown=aiuser:aiuser feature_extraction/ ./feature_extraction/
COPY --chown=aiuser:aiuser utils/ ./utils/
COPY --chown=aiuser:aiuser config/ ./config/

# Weights are mounted at runtime — never committed to image
VOLUME ["/app/weights"]

USER aiuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "2"]
