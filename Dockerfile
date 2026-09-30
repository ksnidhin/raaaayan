# syntax=docker/dockerfile:1
# Raayan — ARM64-compatible Dockerfile
# Base: python:3.12-alpine (linux/amd64 + linux/arm64 — VERIFIED via Docker Hub manifest)
#
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot) — Apache 2.0
# Changes from upstream:
#   - Uses pip + requirements.txt (no pdm.lock required in repo)
#   - aria2 added via apk (arm64 package available in Alpine)
#   - ffmpeg added via apk (arm64 package available in Alpine)
#   - ffpb added (missing from upstream pyproject.toml but imported in helper.py)

FROM python:3.12-alpine AS pybuilder
LABEL stage=builder
WORKDIR /build
COPY requirements.txt .
RUN apk add --no-cache \
        alpine-sdk \
        python3-dev \
        musl-dev \
        linux-headers \
        libffi-dev \
        openssl-dev
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-alpine AS runner
LABEL maintainer="Raayan"
WORKDIR /app

# System packages (all arm64-available in Alpine repos)
RUN apk add --no-cache \
        ffmpeg \
        aria2 \
        ca-certificates \
        curl \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev

# Copy pip-installed packages from builder
COPY --from=pybuilder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=pybuilder /usr/local/bin /usr/local/bin

# Copy source
COPY src/ /app/

# Ensure empty cookie file exists (volume will override if provided)
RUN touch /app/youtube-cookies.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
CMD ["python", "main.py"]
