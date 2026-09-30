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
    try:
        if not url or not isinstance(url, str):
            return False

        parsed = urlparse(url)
        return parsed.netloc.lower() in {"youtube.com", "www.youtube.com", "youtu.be"}

    except Exception:
        return False


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
    parts = text.strip().split(maxsplit=1)
    url = parts[0] if parts else ""
    name = parts[1] if len(parts) > 1 else ""
    return url, name
