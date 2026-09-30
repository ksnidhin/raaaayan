#!/usr/local/bin/python3
# coding: utf-8

# Raayan - constant.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import typing

from pyrogram import Client, types


class BotText:

    start = """
    Welcome to Raayan. Type /help for more information.

    claim me if u caan.

    """

    help = """
1. For YouTube and any websites supported by yt-dlp, just send the link and Raayan will download and send it to you.

2. For specific links use `/spdl {URL}`. Supported: Instagram (Videos, Photos, Reels, IGTV & carousel), Pixeldrain, KrakenFiles.

3. If the bot doesn't work, try again later.

4. Use /settings to change download quality and format.
    """

    about = """
**Raayan**
_claim me if u caan._

Powered by yt-dlp | Built on ytdlbot (Apache 2.0)
Source: https://github.com/tgbot-collection/ytdlbot
    """

    private = "This bot is private. You are not authorized to use it."

    quota_exceeded = "You have exceeded your download quota. Please try again later."

    download_failed = "Download failed! ❌ Please check the link and try again."

    downloading = "Downloading... ⏳"

    uploading = "Uploading... 📤"

    settings_keyboard = [
        [
            types.InlineKeyboardButton("⬆️ High", callback_data="high"),
            types.InlineKeyboardButton("🔼 Medium", callback_data="medium"),
            types.InlineKeyboardButton("🔽 Low", callback_data="low"),
        ],
        [
            types.InlineKeyboardButton("🎞 Video", callback_data="video"),
            types.InlineKeyboardButton("🎵 Audio", callback_data="audio"),
            types.InlineKeyboardButton("📄 Document", callback_data="document"),
        ],
    ]
