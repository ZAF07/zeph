FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" \
    FASTEMBED_CACHE_PATH=/app/.fastembed

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

# Bake the Knowledge embedding model into the image so it isn't downloaded on
# every start.
RUN python -c "from companion.adapters.fastembed.embedder import FastEmbedEmbedder; FastEmbedEmbedder()"

EXPOSE 8000
CMD ["sh", "-c", "python -m companion.prestart && uvicorn companion.main:build_production_app --factory --host 0.0.0.0 --port 8000"]
