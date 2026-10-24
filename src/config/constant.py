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
Send any link from our 4 official supported platforms:
• YouTube (youtube.com, youtu.be)
• Instagram (instagram.com, threads.net)
• Pinterest (pinterest.com, pin.it)
• X / Twitter (x.com, twitter.com)

Features:
• YouTube: instant quality selection buttons (1080p, 720p, 480p, 360p, Audio)
• Instagram: Reels, Videos, Photos & Carousels
• Pinterest: Full original resolution Photos, Videos & GIFs
• X (Twitter): Videos, GIFs & Photos

Commands:
• /settings — Change download quality & format preferences
• /ping — Check bot speed and response time
• /about — About Raayan
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
