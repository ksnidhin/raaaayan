#!/usr/bin/env python3
# coding: utf-8

# Raayan - __init__.py (engine)
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

from urllib.parse import urlparse
from typing import Any, Callable

from engine.generic import YoutubeDownload
from engine.direct import DirectDownload
from engine.pixeldrain import pixeldrain_download
from engine.instagram import InstagramDownload
from engine.krakenfiles import krakenfiles_download


def youtube_entrance(client, bot_message, url, user_id=None):
    youtube = YoutubeDownload(client, bot_message, url, user_id)
    youtube.start()


def direct_entrance(client, bot_message, url, user_id=None):
    dl = DirectDownload(client, bot_message, url, user_id)
    dl.start()


def instagram_handler(client: Any, bot_message: Any, url: str, user_id: int = None) -> None:
    """A wrapper to handle the InstagramDownload class."""
    dl = InstagramDownload(client, bot_message, url, user_id)
    dl.start()


def special_download_entrance(client, bot_message, url: str, user_id=None):
    """Route special URLs to their dedicated engine."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "pixeldrain.com" in host:
        pixeldrain_download(client, bot_message, url, user_id)
    elif "krakenfiles.com" in host:
        krakenfiles_download(client, bot_message, url, user_id)
    elif "instagram.com" in host or "threads.net" in host:
        instagram_handler(client, bot_message, url, user_id)
    else:
        direct_entrance(client, bot_message, url, user_id)
