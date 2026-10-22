#!/usr/local/bin/python3
# coding: utf-8

# Raayan - constant.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import typing

from pyrogram import Client, types

from config.emoji import Emoji, BUTTON_VIDEO_ICON, BUTTON_AUDIO_ICON


class BotText:

    start = """
    Welcome to Raayan. Type /help for more information.

    claim me if u caan.

    """

    help = """
1. For YouTube and any websites supported by yt-dlp, just send the link and Raayan will download and send it to you.

2. For specific links use <code>/spdl &lt;URL&gt;</code>. Supported: Instagram (Videos, Photos, Reels & Stories), Pinterest (Photos, Videos, GIFs), Pixeldrain, KrakenFiles.

3. If the bot doesn't work, try again later.

4. Use /settings to change download quality and format.
    """

    about = """
<b>Raayan</b>
<i>claim me if u caan.</i>

Powered by yt-dlp | Built on ytdlbot (Apache 2.0)
Source: https://github.com/tgbot-collection/ytdlbot
    """

    private = "This bot is private. You are not authorized to use it."

    quota_exceeded = "You have exceeded your download quota. Please try again later."

    download_failed = f"Download failed! {Emoji.error()} Please check the link and try again."

    downloading = f"Downloading... {Emoji.downloading()}"

    uploading = f"Uploading... {Emoji.uploading()}"

    settings_keyboard = [
        [
            types.InlineKeyboardButton("⬆️ High", callback_data="high"),
            types.InlineKeyboardButton("🔼 Medium", callback_data="medium"),
            types.InlineKeyboardButton("🔽 Low", callback_data="low"),
        ],
        [
            types.InlineKeyboardButton("Video", callback_data="video", icon_custom_emoji_id=BUTTON_VIDEO_ICON),
            types.InlineKeyboardButton("Audio", callback_data="audio", icon_custom_emoji_id=BUTTON_AUDIO_ICON),
            types.InlineKeyboardButton("📄 Document", callback_data="document"),
        ],
    ]
