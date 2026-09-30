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


def youtube_entrance(client, bot_message, url):
    youtube = YoutubeDownload(client, bot_message, url)
    youtube.start()


def direct_entrance(client, bot_message, url):
    dl = DirectDownload(client, bot_message, url)
    dl.start()


def instagram_handler(client: Any, bot_message: Any, url: str) -> None:
    """A wrapper to handle the InstagramDownload class."""
    dl = InstagramDownload(client, bot_message, url)
    dl.start()


def special_download_entrance(client, bot_message, url: str):
    """Route special URLs to their dedicated engine."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "pixeldrain.com" in host:
        pixeldrain_download(client, bot_message, url)
    elif "krakenfiles.com" in host:
        krakenfiles_download(client, bot_message, url)
    elif "instagram.com" in host or "threads.net" in host:
        instagram_handler(client, bot_message, url)
    else:
        direct_entrance(client, bot_message, url)
