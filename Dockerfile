# syntax=docker/dockerfile:1

# --- stage 1: install dev dependencies and run the suite -------------------
# The application itself has no runtime dependencies, so the only reason to
# build in stages is to keep pytest and ruff out of the shipped image.
FROM python:3.12-slim AS test

WORKDIR /src
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .
RUN ruff check . && ruff format --check . && python -m pytest

# --- stage 2: runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 10001 pearl
WORKDIR /app

COPY --chown=pearl:pearl pearl/ ./pearl/
COPY --chown=pearl:pearl main.py input.txt ./

USER pearl

# There is no server to poll, so the healthcheck runs the real thing: parse the
# bundled input, place the buyers, and assert the result satisfies the brief.
HEALTHCHECK --interval=30s --timeout=10s --start-period=2s --retries=3 \
    CMD ["python", "main.py", "input.txt", "--stdout", "--verify"]

ENTRYPOINT ["python", "main.py"]
CMD ["input.txt", "--stdout", "--verify"]
