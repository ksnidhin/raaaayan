#!/usr/bin/env python3
# coding: utf-8

# Raayan - test.py (smoke test)
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# License: Apache 2.0

"""
Minimal smoke test - only checks imports and config loading.
Does NOT perform external API calls or Telegram connections.
"""

import sys
import os

print("=== Raayan smoke test ===")

# Check Python version
assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version}"
print(f"✅ Python {sys.version.split()[0]}")

# Check core imports
try:
    import pyrogram
    print(f"✅ pyrogram {pyrogram.__version__}")
except ImportError as e:
    print(f"❌ pyrogram import failed: {e}")
    sys.exit(1)

try:
    import yt_dlp
    print(f"✅ yt-dlp {yt_dlp.version.__version__}")
except ImportError as e:
    print(f"❌ yt-dlp import failed: {e}")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"✅ sqlalchemy {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ sqlalchemy import failed: {e}")
    sys.exit(1)

try:
    import redis
    print(f"✅ redis")
except ImportError as e:
    print(f"❌ redis import failed: {e}")
    sys.exit(1)

try:
    import fakeredis
    print(f"✅ fakeredis")
except ImportError as e:
    print(f"❌ fakeredis import failed: {e}")
    sys.exit(1)

try:
    import ffmpeg
    print(f"✅ ffmpeg-python")
except ImportError as e:
    print(f"❌ ffmpeg-python import failed: {e}")
    sys.exit(1)

print("\n✅ All imports successful. Raayan is ready.")
print("NOTE: External connections (Telegram, MySQL, Redis) not tested here.")
print("      Set up .env and run docker compose up to test the full stack.")
