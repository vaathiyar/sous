FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# CockroachDB CA cert — public certificate, not a secret
RUN mkdir -p /root/.postgresql && \
    curl -sSL https://cockroachlabs.cloud/clusters/297b2431-6175-43a0-b638-f23313d663a5/cert \
    -o /root/.postgresql/root.crt

# Install dependencies (cached layer — only invalidated when lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Pre-bake the Silero VAD model so the first session has no cold-start download
RUN uv run python -c "from livekit.plugins import silero; silero.VAD.load()"

# Copy application source
COPY backend/ backend/
COPY chef/ chef/
COPY shared/ shared/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
