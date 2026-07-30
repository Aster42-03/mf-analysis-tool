FROM python:3.12-slim
LABEL authors="Aster42"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/src

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen --no-install-project --no-group test

COPY . .

CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]