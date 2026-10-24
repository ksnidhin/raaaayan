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
from engine.pinterest import PinterestDownload
from engine.x import XDownload
from utils import get_supported_platform


def youtube_entrance(client, bot_message, url, user_id=None, resolution=None):
    youtube = YoutubeDownload(client, bot_message, url, user_id, resolution)
    youtube.start()


def direct_entrance(client, bot_message, url, user_id=None):
    dl = DirectDownload(client, bot_message, url, user_id)
    dl.start()


def instagram_handler(client: Any, bot_message: Any, url: str, user_id: int = None) -> None:
    """A wrapper to handle the InstagramDownload class."""
    dl = InstagramDownload(client, bot_message, url, user_id)
    dl.start()


def pinterest_handler(client: Any, bot_message: Any, url: str, user_id: int = None) -> None:
    """A wrapper to handle the PinterestDownload class."""
    dl = PinterestDownload(client, bot_message, url, user_id)
    dl.start()


def x_handler(client: Any, bot_message: Any, url: str, user_id: int = None) -> None:
    """A wrapper to handle the XDownload class."""
    dl = XDownload(client, bot_message, url, user_id)
    dl.start()


def special_download_entrance(client, bot_message, url: str, user_id=None):
    """Route supported URLs to their dedicated engine."""
    platform = get_supported_platform(url)

    if platform == "instagram":
        instagram_handler(client, bot_message, url, user_id)
    elif platform == "pinterest":
        pinterest_handler(client, bot_message, url, user_id)
    elif platform == "x":
        x_handler(client, bot_message, url, user_id)
    elif platform == "youtube":
        youtube_entrance(client, bot_message, url, user_id)
    elif "pixeldrain.com" in url:
        pixeldrain_download(client, bot_message, url, user_id)
    elif "krakenfiles.com" in url:
        krakenfiles_download(client, bot_message, url, user_id)
    else:
        bot_message.edit_text("⚠️ Unsupported link.\n\nRaayan only processes official links from:\n• YouTube\n• Instagram\n• Pinterest\n• X / Twitter")
