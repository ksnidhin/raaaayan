# Raayan

**claim me if u caan.**

A Telegram bot that downloads videos and media from YouTube and hundreds of other websites — rebranded from [ytdlbot](https://github.com/tgbot-collection/ytdlbot) and deployment-prepared for ARM64 VPS.

---

## What it is

Raayan is a Telegram bot powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp). Send it a link and it downloads and sends the media back to you in Telegram.

> This is a fork of [ytdlbot](https://github.com/tgbot-collection/ytdlbot) by Benny (Apache 2.0). The engine, downloader logic, and database schema are preserved from upstream. Only user-facing branding and deployment configuration have been changed.

---

## Features

The following features are confirmed from source-code inspection:

- ✅ Download from YouTube and all [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- ✅ Download from Instagram (Videos, Photos, Reels, IGTV, carousel) via sidecar service
- ✅ Download from Pixeldrain
- ✅ Download from KrakenFiles
- ✅ Quality selection: High / Medium / Low
- ✅ Format selection: Video / Audio / Document
- ✅ Download progress bar
- ✅ Per-user quota tracking (free + paid)
- ✅ Daily free quota reset (APScheduler cron)
- ✅ Redis caching with fakeredis fallback
- ✅ Optional aria2c accelerated downloads
- ✅ Optional FFmpeg merging
- ✅ YouTube cookie support (for age-restricted content)
- ✅ VIP/payment system (optional, requires Telegram payment provider)

---

## Architecture

```
Telegram User
      │
      ▼
  Pyrogram Bot (main.py)
      │
      ├── /start /help /about /ping /settings
      ├── /ytdl <url>         → YoutubeDownload (yt-dlp)
      ├── /spdl <url>         → special_download_entrance
      │                           ├── instagram.com → InstagramDownload
      │                           │       └── http://instagram:15000 (sidecar)
      │                           ├── pixeldrain.com → pixeldrain_download
      │                           ├── krakenfiles.com → krakenfiles_download
      │                           └── other → DirectDownload (requests / aria2c)
      └── <plain url>         → YoutubeDownload (yt-dlp)

BaseDownloader
  ├── quota check (MySQL via SQLAlchemy)
  ├── download to tempfile.TemporaryDirectory (auto-cleaned)
  ├── optional FFmpeg merge
  └── upload to Telegram → cleanup

Scheduler (APScheduler)
  └── daily midnight → reset_free() for all users

Persistence:
  ├── MySQL — users, settings, payments tables
  └── Redis — caching (fakeredis fallback if Redis unavailable)
```

---

## Requirements

- Docker + Docker Compose (recommended)
- ARM64 VPS (linux/aarch64) — all images verified
- Telegram Bot Token, App ID, App Hash (from https://my.telegram.org)
- MySQL database
- Redis (optional — fakeredis used if not configured)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_ID` | ✅ | — | Telegram App ID |
| `APP_HASH` | ✅ | — | Telegram App Hash |
| `BOT_TOKEN` | ✅ | — | Telegram Bot Token |
| `OWNER` | ✅ | — | Owner Telegram user ID(s), comma-separated |
| `DB_DSN` | ✅ | — | MySQL DSN: `mysql+pymysql://user:pass@mysql/db` |
| `MYSQL_ROOT_PASSWORD` | ✅ (Docker) | — | MySQL root password for Docker service |
| `MYSQL_DATABASE` | ✅ (Docker) | raayan | MySQL database name |
| `MYSQL_USER` | ✅ (Docker) | raayan | MySQL user |
| `MYSQL_PASSWORD` | ✅ (Docker) | — | MySQL user password |
| `REDIS_HOST` | optional | — | Redis hostname (empty = fakeredis) |
| `WORKERS` | optional | 100 | Pyrogram worker thread count |
| `AUTHORIZED_USER` | optional | — | Comma-separated user IDs (empty = all users) |
| `ENABLE_FFMPEG` | optional | False | Enable FFmpeg for video merging |
| `AUDIO_FORMAT` | optional | m4a | Audio format (mp3, wav, etc.) |
| `M3U8_SUPPORT` | optional | False | Enable HLS/m3u8 streams |
| `ENABLE_ARIA2` | optional | False | Enable aria2c for direct downloads |
| `ENABLE_VIP` | optional | False | Enable paid quota features |
| `PROVIDER_TOKEN` | optional | — | Telegram payment provider token |
| `FREE_DOWNLOAD` | optional | 3 | Free downloads per user per day |
| `TOKEN_PRICE` | optional | 10 | Downloads per 1 USD |
| `TMPFILE_PATH` | optional | system tmp | Custom temp directory for downloads |
| `POTOKEN` | optional | — | YouTube PO token |
| `BROWSERS` | optional | firefox | Browser for cookie extraction |

---

## ARM64 Deployment

### Verified ARM64 components

| Component | Image/Package | ARM64 Status |
|---|---|---|
| Python | `python:3.12-alpine` | VERIFIED — Docker Hub multi-arch manifest includes `linux/arm64` |
| Redis | `redis:7-alpine` | VERIFIED — Docker Hub multi-arch manifest includes `linux/arm64` |
| MySQL | `mysql:8.0` | VERIFIED — Docker Hub multi-arch manifest includes `linux/arm64` |
| ffmpeg | Alpine `ffmpeg` apk | VERIFIED — Available in Alpine `aarch64` package repos |
| aria2 | Alpine `aria2` apk | VERIFIED — Available in Alpine `aarch64` package repos |
| Pyrogram | PyPI | VERIFIED — Pure Python + tgcrypto (has Alpine musl-compatible wheels) |
| yt-dlp | PyPI | VERIFIED — Pure Python |
| SQLAlchemy | PyPI | VERIFIED — Pure Python |
| Redis-py | PyPI | VERIFIED — Pure Python |

> **NOT VERIFIED**: Instagram sidecar service. The bot calls `http://instagram:15000` which is a separate service not included in this repository. You must provide this service yourself if Instagram downloads are needed. The bot will fail gracefully for Instagram URLs if the sidecar is not running.

### Deploy on ARM64 VPS

```bash
# 1. Clone the repository
git clone https://github.com/ksnidhin/raaaayan.git
cd raaaayan

# 2. Configure environment
cp .env.example .env
nano .env   # fill in APP_ID, APP_HASH, BOT_TOKEN, OWNER, passwords

# 3. Build and start
docker compose build
docker compose up -d

# 4. Check logs
docker compose logs -f raayan

# 5. Check service health
docker compose ps
```

### Explicit ARM64 build

If Docker does not auto-detect your architecture:

```bash
docker buildx build --platform linux/arm64 -t raayan:latest .
```

---

## YouTube Cookies

For age-restricted or members-only YouTube content, provide cookies:

```bash
# Export cookies from your browser using an extension (e.g. "Get cookies.txt LOCALLY")
# Save as youtube-cookies.txt in Netscape format in the project root
# The file is already volume-mounted into the container
```

---

## Troubleshooting

**Bot does not start — `DB_DSN` error**
- Ensure MySQL is running and healthy before the bot starts
- `docker compose ps` — check mysql service health
- `docker compose logs mysql` — check for startup errors

**Redis connection failed**
- If `REDIS_HOST` is empty, fakeredis is used automatically (no persistence)
- `docker compose logs redis` — check Redis health

**Instagram downloads fail**
- The Instagram engine requires a separate sidecar service at `http://instagram:15000`
- This sidecar is NOT included in this repository
- Without the sidecar, Instagram URLs will produce an error

**YouTube 403/bot detection**
- Set `POTOKEN` in `.env` (see [PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide))
- Provide cookies via `youtube-cookies.txt`

**`aria2c` not found**
- Set `ENABLE_ARIA2=False` (aria2c is included in the Docker image but may not be on bare metal)

---

## License & Attribution

This project is a fork of **ytdlbot** by Benny (benny.think@gmail.com).

- Upstream repository: https://github.com/tgbot-collection/ytdlbot
- License: [Apache License 2.0](LICENSE)

The `krakenfiles.py` and `pixeldrain.py` engines were originally authored by **SanujaNS** (sanujas@sanuja.biz).

This fork (Raayan) contains:
- Rebranded user-facing text (bot messages, README)
- ARM64-compatible Docker configuration
- MySQL image changed from `ubuntu/mysql:8.0-22.04_beta` to `mysql:8.0` (official ARM64-verified image)
- MySQL credentials moved from hard-coded values to environment variables
- `krakenfiles.py` bug fix: replaced `soup.xpath()` (unsupported by BeautifulSoup) with `soup.find()`
- Added `ffpb` dependency (imported in source but missing from upstream `pyproject.toml`)

All engine code, downloader logic, database schema, and architecture are preserved from upstream.
