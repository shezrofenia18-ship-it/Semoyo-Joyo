FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AUTO_START_LOCAL_PG=false

WORKDIR /app

# curl hanya untuk HEALTHCHECK. Tidak perlu build-essential/libpq-dev:
# semua dependensi (asyncpg, bcrypt, pillow, dll) tersedia sebagai wheel siap pakai.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependensi lebih dulu agar layer ini ter-cache selama requirements.txt tidak berubah
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Salin source code (lihat .dockerignore: pgdata, uploads, .env, cache, tes tidak ikut)
COPY . .
RUN mkdir -p /app/uploads

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8001/api/health || exit 1

# 1 worker: lifespan (create tables + seed) hanya berjalan sekali sehingga tidak terjadi race saat seeding.
# Skala horizontal cukup dengan menambah replika container di Coolify bila diperlukan.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips", "*"]
