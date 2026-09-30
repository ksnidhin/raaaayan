#!/usr/bin/env python3
# coding: utf-8

# Raayan - helper.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import functools
import logging
import os
import pathlib
import re
import subprocess
import threading
import time
from http import HTTPStatus
from io import StringIO

import ffmpeg
import ffpb
import filetype
import pyrogram
import requests
import yt_dlp
from bs4 import BeautifulSoup
from pyrogram import types
from tqdm import tqdm

from config import (
    AUDIO_FORMAT,
    CAPTION_URL_LENGTH_LIMIT,
    ENABLE_ARIA2,
    TG_NORMAL_MAX_SIZE,
)
from utils import shorten_url, sizeof_fmt


def debounce(wait_seconds):
    """
    Thread-safe debounce decorator for functions that take a message with chat.id and msg.id attributes.
    The function will only be called if it hasn't been called with the same chat.id and msg.id in the last 'wait_seconds'.
    """

    def decorator(func):
        last_called = {}
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            now = time.time()

            # Assuming the first argument is the message object with chat.id and msg.id
            bot_msg = args[0]._bot_msg
            key = (bot_msg.chat.id, bot_msg.id)

            with lock:
                if key not in last_called or now - last_called[key] >= wait_seconds:
                    last_called[key] = now
                    return func(*args, **kwargs)

        return wrapper

    return decorator


def get_metadata(video_path: pathlib.Path) -> dict:
    """Use ffprobe to extract metadata from a media file."""
    try:
        probe = ffmpeg.probe(str(video_path))
        return probe
    except Exception as e:
        logging.warning("ffprobe failed for %s: %s", video_path, e)
        return {}


def get_caption(url: str, video_path) -> str:
    if isinstance(video_path, pathlib.Path):
        meta = get_metadata(video_path)
        file_name = video_path.name
        file_size = sizeof_fmt(video_path.stat().st_size)
        duration = ""
        try:
            fmt = meta.get("format", {})
            secs = float(fmt.get("duration", 0))
            m, s = divmod(int(secs), 60)
            duration = f"{m:02d}:{s:02d}"
        except Exception:
            pass
        short_url = shorten_url(url, CAPTION_URL_LENGTH_LIMIT)
        return f"`{file_name}`\n📦 {file_size}  ⏱ {duration}\n🔗 {short_url}"
    return shorten_url(url, CAPTION_URL_LENGTH_LIMIT)


def run_ffmpeg_convert(input_path: pathlib.Path, output_path: pathlib.Path):
    """Convert media using ffmpeg-python."""
    try:
        (
            ffmpeg.input(str(input_path))
            .output(str(output_path))
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        logging.error("FFmpeg conversion failed: %s", e)
        return False
