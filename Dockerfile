FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY backend/verify_samples.py ./verify_samples.py
WORKDIR /app
COPY deploy/runtime-assets.tar.gz deploy/runtime-assets.json ./deploy/
COPY data/samples ./data/samples
COPY data/seed ./data/seed
COPY data/templates ./data/templates
COPY data/kb/gaon ./data/kb/gaon
COPY data/kb/policy/std_*.txt ./data/kb/policy/
ENV PATH="/app/backend/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app/backend
CMD ["python", "-m", "app.scripts.deploy_start"]
