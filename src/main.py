#!/usr/local/bin/python3
# coding: utf-8

# Raayan - main.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import html as html_lib
import logging
import os
import re
import threading
import time
import typing
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import psutil
import pyrogram.errors
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, enums, filters, types

from config import (
    APP_HASH,
    APP_ID,
    AUTHORIZED_USER,
    BOT_TOKEN,
    ENABLE_ARIA2,
    ENABLE_FFMPEG,
    M3U8_SUPPORT,
    ENABLE_VIP,
    OWNER,
    PROVIDER_TOKEN,
    TOKEN_PRICE,
    BotText,
    Emoji,
)
from database.cache import Redis
from database.model import (
    credit_account,
    get_format_settings,
    get_free_quota,
    get_paid_quota,
    get_quality_settings,
    init_user,
    reset_free,
    set_user_settings,
)
from engine import direct_entrance, youtube_entrance, special_download_entrance
from utils import extract_url_and_name, is_youtube, sizeof_fmt, timeof_fmt

logging.info("Authorized users are %s", AUTHORIZED_USER)
logging.getLogger("apscheduler.executors.default").propagate = False


def create_app(name: str, workers: int = 64) -> Client:
    return Client(
        name,
        APP_ID,
        APP_HASH,
        bot_token=BOT_TOKEN,
        workers=workers,
        parse_mode=enums.ParseMode.HTML,
    )


app = create_app("main")


def private_use(func):
    def wrapper(client: Client, message: types.Message):
        chat_id = getattr(message.from_user, "id", None)

        # In groups/supergroups: only process commands or messages containing links
        if message.chat.type != enums.ChatType.PRIVATE:
            text = getattr(message, "text", "") or ""
            # Allow commands, raw http links, or replies to messages
            has_link = "http" in text or (
                getattr(message, "reply_to_message", None)
                and "http" in (getattr(message.reply_to_message, "text", "") or "")
            )
            if not text.startswith("/") and not has_link:
                logging.debug("Ignored non-command/non-link in group: %s", text)
                return

        # authorized users check
        if AUTHORIZED_USER:
            users = [int(i) for i in AUTHORIZED_USER.split(",")]
        else:
            users = []

        if users and chat_id and chat_id not in users:
            message.reply_text(BotText.private, quote=True)
            return

        return func(client, message)

    return wrapper


@app.on_message(filters.command(["start"]))
def start_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)
    logging.info("%s welcome to Raayan!", user_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    free, paid = get_free_quota(user_id), get_paid_quota(user_id)
    client.send_message(
        chat_id,
        BotText.start + f"You have {free} free and {paid} paid quota.",
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["help"]))
def help_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    client.send_message(chat_id, BotText.help, disable_web_page_preview=True)


@app.on_message(filters.command(["about"]))
def about_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    client.send_message(chat_id, BotText.about)


@app.on_message(filters.command(["ping"]))
def ping_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)

    start_time = int(round(time.time() * 1000))
    reply: types.Message = client.send_message(chat_id, "Pinging...")
    end_time = int(round(time.time() * 1000))
    ping_time = end_time - start_time

    client.edit_message_text(
        chat_id=reply.chat.id,
        message_id=reply.id,
        text=f"Pong! {Emoji.ping()} <code>{ping_time} ms</code>",
    )


@app.on_message(filters.command(["settings"]))
def settings_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)
    quality = get_quality_settings(user_id)
    fmt = get_format_settings(user_id)
    client.send_message(
        chat_id,
        f"<b>Current settings:</b>\n{Emoji.settings()} Quality: <code>{quality}</code>\n{Emoji.package()} Format: <code>{fmt}</code>\n\nChoose your preferred quality and format:",
        reply_markup=types.InlineKeyboardMarkup(BotText.settings_keyboard),
    )


@app.on_callback_query(filters.regex(r"^(high|medium|low|video|audio|document)$"))
def settings_callback(client: Client, callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    init_user(user_id)

    quality_options = {"high", "medium", "low"}
    format_options = {"video", "audio", "document"}

    if data in quality_options:
        set_user_settings(user_id, quality=data)
        callback_query.answer(f"Quality set to {data} ✅")
    elif data in format_options:
        set_user_settings(user_id, format_=data)
        callback_query.answer(f"Format set to {data} ✅")
    else:
        callback_query.answer("Unknown setting")
        return

    quality = get_quality_settings(user_id)
    fmt = get_format_settings(user_id)
    client.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.id,
        text=f"<b>Current settings:</b>\n{Emoji.settings()} Quality: <code>{quality}</code>\n{Emoji.package()} Format: <code>{fmt}</code>\n\nChoose your preferred quality and format:",
        reply_markup=types.InlineKeyboardMarkup(BotText.settings_keyboard),
    )


@app.on_message(filters.command(["spdl"]))
@private_use
def spdl_handler(client: Client, message: types.Message):
    """Special download handler for Instagram, Pixeldrain, KrakenFiles."""
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)

    url, _ = extract_url_and_name(message.text or "")
    if not url and message.reply_to_message and message.reply_to_message.text:
        url, _ = extract_url_and_name(message.reply_to_message.text)

    if not url:
        message.reply_text("Usage: <code>/spdl &lt;URL&gt;</code> or reply to a message containing a link.", quote=True)
        return

    bot_msg = message.reply_text(f"Searching... {Emoji.get_search_emoji()}", quote=True)
    threading.Thread(
        target=special_download_entrance,
        args=(client, bot_msg, url, user_id),
        daemon=True,
    ).start()


def get_yt_quality_keyboard():
    return types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("📹 1080p", callback_data="yt_q|1080"),
            types.InlineKeyboardButton("📹 720p", callback_data="yt_q|720"),
        ],
        [
            types.InlineKeyboardButton("📹 480p", callback_data="yt_q|480"),
            types.InlineKeyboardButton("📹 360p", callback_data="yt_q|360"),
        ],
        [
            types.InlineKeyboardButton("🎵 Audio Only (M4A/MP3)", callback_data="yt_q|audio"),
        ]
    ])


def send_youtube_quality_prompt(client: Client, message: types.Message, url: str, user_id: int):
    """Instantly send YouTube quality selection buttons without delay."""
    keyboard = get_yt_quality_keyboard()
    bot_msg = message.reply_text("Choose download quality:", reply_markup=keyboard, quote=True)

    try:
        redis = Redis()
        redis.set(f"yt_url:{bot_msg.chat.id}:{bot_msg.id}", url, ex=3600)
    except Exception as e:
        logging.warning("Redis set error: %s", e)

    # In background, try to fetch the video title quickly to enhance the card header
    def _fetch_title():
        cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cookies.txt"))
        if not os.path.exists(cookie_path):
            cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "youtube-cookies.txt"))
        if not os.path.exists(cookie_path):
            cookie_path = "/app/youtube-cookies.txt"

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "js_runtimes": {"node": {}},
            "extract_flat": True,
        }
        if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
            ydl_opts["cookiefile"] = cookie_path
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title") if info else None
                if title:
                    safe_title = html_lib.escape(title)
                    bot_msg.edit_text(f"{Emoji.clapper()} <b>{safe_title}</b>\n\nChoose download quality:", reply_markup=keyboard)
        except Exception:
            pass

    threading.Thread(target=_fetch_title, daemon=True).start()


@app.on_message(filters.command(["ytdl"]))
@private_use
def ytdl_handler(client: Client, message: types.Message):
    """Force yt-dlp download for a given URL (group-compatible via /ytdl)."""
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)

    url, _ = extract_url_and_name(message.text or "")
    if not url and message.reply_to_message and message.reply_to_message.text:
        url, _ = extract_url_and_name(message.reply_to_message.text)

    if not url:
        message.reply_text("Usage: <code>/ytdl &lt;URL&gt;</code> or reply to a message containing a link.", quote=True)
        return

    if is_youtube(url):
        send_youtube_quality_prompt(client, message, url, user_id)
    else:
        bot_msg = message.reply_text(f"Searching... {Emoji.get_search_emoji()}", quote=True)
        threading.Thread(
            target=youtube_entrance,
            args=(client, bot_msg, url, user_id),
            daemon=True,
        ).start()


@app.on_message(filters.text & ~filters.command(
    ["start", "help", "about", "ping", "settings", "spdl", "ytdl", "credit", "check"]
))
@private_use
def url_handler(client: Client, message: types.Message):
    """Handle plain URLs sent to the bot in private chat or groups."""
    chat_id = message.chat.id
    user_id = message.from_user.id if getattr(message, 'from_user', None) else chat_id
    init_user(user_id)

    url, _ = extract_url_and_name(message.text or "")
    if not url and message.reply_to_message and message.reply_to_message.text:
        url, _ = extract_url_and_name(message.reply_to_message.text)

    if not url or not url.startswith("http"):
        return

    # Route to appropriate engine
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if is_youtube(url):
        send_youtube_quality_prompt(client, message, url, user_id)
    elif "instagram.com" in host or "threads.net" in host:
        bot_msg = message.reply_text(f"Searching... {Emoji.get_search_emoji()}", quote=True)
        threading.Thread(
            target=special_download_entrance,
            args=(client, bot_msg, url, user_id),
            daemon=True,
        ).start()
    else:
        bot_msg = message.reply_text(f"Searching... {Emoji.get_search_emoji()}", quote=True)
        threading.Thread(
            target=youtube_entrance,
            args=(client, bot_msg, url, user_id),
            daemon=True,
        ).start()


@app.on_callback_query(filters.regex(r"^yt_q\|"))
def yt_quality_callback(client: Client, callback_query: types.CallbackQuery):
    data = callback_query.data
    _, quality_choice = data.split("|", 1)
    user_id = callback_query.from_user.id
    init_user(user_id)

    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id

    url = None
    try:
        redis = Redis()
        url = redis.get(f"yt_url:{chat_id}:{message_id}")
    except Exception as e:
        logging.warning("Redis get error: %s", e)

    if not url:
        original_msg = callback_query.message.reply_to_message
        if original_msg and original_msg.text:
            url, _ = extract_url_and_name(original_msg.text)
            if not url and original_msg.reply_to_message and original_msg.reply_to_message.text:
                url, _ = extract_url_and_name(original_msg.reply_to_message.text)

    if not url:
        callback_query.answer("Video URL expired or not found. Please send the link again.", show_alert=True)
        return

    label = f"{quality_choice}p" if quality_choice.isdigit() else quality_choice.capitalize()
    callback_query.answer(f"Selected {label}")
    try:
        callback_query.message.edit_text(f"Downloading {label}... {Emoji.downloading()}", reply_markup=None)
    except Exception as e:
        logging.warning("Failed to edit callback message: %s", e)

    threading.Thread(
        target=youtube_entrance,
        args=(client, callback_query.message, url, user_id, quality_choice),
        daemon=True,
    ).start()


@app.on_callback_query(filters.regex(r"^dl_"))
def dl_callback(client: Client, callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    init_user(user_id)

    original_msg = callback_query.message.reply_to_message
    text_to_check = original_msg.text if (original_msg and original_msg.text) else ""
    url, _ = extract_url_and_name(text_to_check)
    if not url and original_msg and original_msg.reply_to_message and original_msg.reply_to_message.text:
        url, _ = extract_url_and_name(original_msg.reply_to_message.text)

    if not url:
        callback_query.answer("No URL found.")
        return

    fmt = "video" if "video" in data else "audio"
    set_user_settings(user_id, format_=fmt)

    callback_query.message.edit_text(f"Downloading... {Emoji.downloading()}", reply_markup=None)

    threading.Thread(
        target=youtube_entrance,
        args=(client, callback_query.message, url, user_id),
        daemon=True,
    ).start()


@app.on_message(filters.command(["credit"]))
def credit_handler(client: Client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in OWNER:
        message.reply_text(f"Owner only. {Emoji.error()}", quote=True)
        return

    text = message.text.split()
    if len(text) < 3:
        message.reply_text("Usage: /credit <user_id> <amount>", quote=True)
        return

    try:
        target_id = int(text[1])
        amount = int(text[2])
    except ValueError:
        message.reply_text("User ID and amount must be integers.", quote=True)
        return

    init_user(target_id)
    credit_account(target_id, amount)
    free, paid = get_free_quota(target_id), get_paid_quota(target_id)
    message.reply_text(f"Added {amount} credits to {target_id}.\nNew Balance: {free} free, {paid} paid.", quote=True)


@app.on_message(filters.command(["check"]))
def check_handler(client: Client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in OWNER:
        message.reply_text(f"Owner only. {Emoji.error()}", quote=True)
        return

    text = message.text.split()
    if len(text) < 2:
        message.reply_text("Usage: /check <user_id>", quote=True)
        return

    try:
        target_id = int(text[1])
    except ValueError:
        message.reply_text("User ID must be an integer.", quote=True)
        return

    init_user(target_id)
    free, paid = get_free_quota(target_id), get_paid_quota(target_id)
    message.reply_text(f"User {target_id} has {free} free and {paid} paid quota.", quote=True)


# ---- Scheduled jobs ----


def reset_daily_quota():
    """Reset free download quota for all users. Called by scheduler."""
    logging.info("Running daily quota reset")
    try:
        reset_free()
    except Exception as e:
        logging.error("Quota reset failed: %s", e)


scheduler = BackgroundScheduler()
# Reset free quota every day at midnight UTC
scheduler.add_job(reset_daily_quota, "cron", hour=0, minute=0)
scheduler.start()

logging.info("Raayan starting...")
app.run()
