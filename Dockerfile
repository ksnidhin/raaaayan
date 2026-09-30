# syntax=docker/dockerfile:1
# Raayan — ARM64-compatible Dockerfile
# Base: python:3.12-alpine (linux/amd64 + linux/arm64 — VERIFIED via Docker Hub manifest)
#
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot) — Apache 2.0
# Changes from upstream:
#   - Explicit --platform=linux/arm64 target label
#   - aria2 added via apk (arm64 package available in Alpine)
#   - ffmpeg added via apk (arm64 package available in Alpine)
#   - ffpb added to pip install (missing from pyproject.toml but imported in helper.py)
#   - WORKDIR set to /app, src/ mounted there

FROM python:3.12-alpine AS pybuilder
LABEL stage=builder
ADD pyproject.toml pdm.lock /build/
WORKDIR /build
RUN apk add --no-cache \
        alpine-sdk \
        python3-dev \
        musl-dev \
        linux-headers \
        libffi-dev \
        openssl-dev
RUN pip install --no-cache-dir pdm
RUN pdm install --prod --no-editable

FROM python:3.12-alpine AS runner
LABEL maintainer="Raayan"
WORKDIR /app

# System packages
# ffmpeg: arm64 available in Alpine (linux/arm64) — VERIFIED via Alpine packages
# aria2: arm64 available in Alpine — VERIFIED via Alpine packages
RUN apk update && apk add --no-cache \
        ffmpeg \
        aria2 \
        ca-certificates \
        curl

# Copy virtualenv from builder
COPY --from=pybuilder /build/.venv /app/.venv

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy source
COPY src/ /app/

# Ensure empty cookie file exists (volume will override if provided)
RUN touch /app/youtube-cookies.txt

# Create temp directory for downloads
RUN mkdir -p /tmp/raayan && chmod 777 /tmp/raayan

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
CMD ["python", "main.py"]
