#!/usr/bin/env python3
# coding: utf-8

# Raayan - __init__.py (utils)
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging
import pathlib
import re
import shutil
import tempfile
import time
import uuid
from http.cookiejar import MozillaCookieJar
from urllib.parse import quote_plus, urlparse

import ffmpeg


def sizeof_fmt(num: int, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def timeof_fmt(seconds: int | float):
    periods = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result


def is_youtube(url: str) -> bool:
    return get_supported_platform(url) == "youtube"


def get_supported_platform(url: str) -> str | None:
    """Sub-millisecond whitelist filter for official domains only.
    
    Returns one of: 'youtube', 'instagram', 'pinterest', 'x', or None.
    """
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return None

        host = parsed.netloc.lower()
        if ":" in host:
            host = host.split(":")[0]

        if not host:
            return None

        # 1. Official YouTube
        if host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com"):
            return "youtube"

        # 2. Official Instagram & Threads
        if host == "instagram.com" or host.endswith(".instagram.com") or host == "threads.net" or host.endswith(".threads.net"):
            return "instagram"

        # 3. Official Pinterest
        if host == "pin.it" or host.endswith(".pin.it") or host == "pinterest.com" or host.endswith(".pinterest.com") or host.startswith("pinterest."):
            return "pinterest"

        # 4. Official X / Twitter
        if host == "x.com" or host.endswith(".x.com") or host == "twitter.com" or host.endswith(".twitter.com") or host == "t.co" or host.endswith(".t.co"):
            return "x"

        return None
    except Exception:
        return None


def adjust_formats(formats):
    # high: best quality 1080P, 2K, 4K, 8K
    # medium: 720P
    # low: 480P
    mapping = {"high": [], "medium": [720], "low": [480]}
    return mapping


def shorten_url(url: str, limit: int = 50) -> str:
    if len(url) <= limit:
        return url
    return url[:limit] + "..."


def extract_url_and_name(text: str):
    """Extract URL and optional filename from a message text."""
    if not text:
        return "", ""
    import re
    match = re.search(r"(https?://[^\s]+)", text)
    if not match:
        return "", ""
    url = match.group(1)
    name_part = text[match.end():].strip()
    return url, name_part
