# ---------- base: lo que necesita la aplicación ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src ./src
COPY datos ./datos

# ---------- pruebas: agrega pytest, Ruff y la carpeta tests ----------
FROM base AS pruebas
COPY requirements-dev.txt pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY tests ./tests
COPY docs ./docs
CMD ["sh", "-c", "ruff check src tests && pytest -v --cov=src --cov-report=term-missing --cov-fail-under=80"]

# ---------- produccion: imagen final (la que usa Render) ----------
FROM base AS produccion
RUN useradd --create-home cleanpro && chown cleanpro /app
USER cleanpro
EXPOSE 8000
# Render (y otras plataformas) indican el puerto en la variable PORT; en local se usa 8000.
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
