#!/usr/bin/env python3
# coding: utf-8

# Raayan - base.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import hashlib
import json
import logging
import re
import tempfile
import uuid
from abc import ABC, abstractmethod
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from typing import final

import ffmpeg
import filetype
from pyrogram import enums, types
from tqdm import tqdm

from config import TG_NORMAL_MAX_SIZE, Types
from database import Redis
from database.model import (
    check_quota,
    get_format_settings,
    get_free_quota,
    get_paid_quota,
    get_quality_settings,
    use_quota,
)
from engine.helper import debounce, sizeof_fmt


def generate_input_media(file_paths: list, cap: str) -> list:
    input_media = []
    for path in file_paths:
        mime = filetype.guess_mime(path)
        if mime and "video" in mime:
            input_media.append(types.InputMediaVideo(media=path))
        elif mime and "image" in mime:
            input_media.append(types.InputMediaPhoto(media=path))
        elif mime and "audio" in mime:
            input_media.append(types.InputMediaAudio(media=path))
        else:
            input_media.append(types.InputMediaDocument(media=path))

    if input_media:
        input_media[0].caption = cap
    return input_media


class BaseDownloader(ABC):
    def __init__(self, client, bot_msg, url: str):
        self._client = client
        self._url = url
        # chat id is the same for private chat
        self._chat_id = self._from_user = bot_msg.chat.id
        if bot_msg.chat.type == enums.ChatType.GROUP or bot_msg.chat.type == enums.ChatType.SUPERGROUP:
            # if in group, we need to find out who send the message
            self._from_user = bot_msg.reply_to_message.from_user.id
        self._id = bot_msg.id
        self._tempdir = tempfile.TemporaryDirectory(prefix="raayan-")
        self._bot_msg = bot_msg
        self._redis = Redis()
        self._quality = get_quality_settings(self._chat_id)
        self._format = get_format_settings(self._chat_id)

    def __del__(self):
        self._tempdir.cleanup()

    def _record_usage(self):
        free, paid = get_free_quota(self._from_user), get_paid_quota(self._from_user)
        logging.info("User %s has %s free and %s paid quota", self._from_user, free, paid)
        if free + paid < 0:
            raise Exception("Usage limit exceeded")

        use_quota(self._from_user)

    @staticmethod
    def __remove_bash_color(text):
        return re.sub(r"\u001b|\[0;94m|\u001b\[0m|\[0;32m|\[0m|\[0;33m", "", text)

    @staticmethod
    def __tqdm_progress(desc, total, finished, speed="", eta=""):
        def more(title, initial):
            if initial:
                return f"{title} {initial}"
            else:
                return ""

        f = StringIO()
        tqdm(
            total=total,
            initial=finished,
            file=f,
            ascii=False,
            unit_scale=True,
            ncols=30,
            bar_format="{l_bar}{bar} |{n_fmt}/{total_fmt} ",
        )
        raw_output = f.getvalue()
        tqdm_output = raw_output.split("|")
        progress = f"`[{tqdm_output[1]}]`"
        detail = tqdm_output[2].replace("[A", "")
        text = f"""
    {desc}

    {progress}
    {detail}
    {more("Speed:", speed)}
    {more("ETA:", eta)}
        """
        f.close()
        return text

    @debounce(5)
    def download_hook(self, d: dict):
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed = d.get("speed")
            eta = d.get("eta")

            speed_str = f"{sizeof_fmt(speed)}/s" if speed else ""
            eta_str = f"{eta}s" if eta else ""

            text = self.__tqdm_progress(
                "Downloading...",
                total,
                downloaded,
                speed_str,
                eta_str,
            )
            try:
                self._bot_msg.edit_text(text)
            except Exception:
                pass

    @abstractmethod
    def _setup_formats(self) -> list | None:
        pass

    @abstractmethod
    def _download(self, formats=None):
        pass

    def _upload(self, file_paths: list, caption: str):
        """Upload files to Telegram."""
        if not file_paths:
            self._bot_msg.edit_text("No files to upload. ❌")
            return

        try:
            if len(file_paths) == 1:
                path = file_paths[0]
                mime = filetype.guess_mime(path)
                self._bot_msg.edit_text("Uploading... 📤")

                if mime and "video" in mime:
                    self._client.send_video(
                        self._chat_id,
                        path,
                        caption=caption,
                        supports_streaming=True,
                        reply_to_message_id=self._id,
                    )
                elif mime and "audio" in mime:
                    self._client.send_audio(
                        self._chat_id,
                        path,
                        caption=caption,
                        reply_to_message_id=self._id,
                    )
                else:
                    self._client.send_document(
                        self._chat_id,
                        path,
                        caption=caption,
                        reply_to_message_id=self._id,
                    )
            else:
                # Album upload
                input_media = generate_input_media(file_paths, caption)
                self._bot_msg.edit_text("Uploading album... 📤")
                self._client.send_media_group(
                    self._chat_id,
                    input_media,
                    reply_to_message_id=self._id,
                )

            self._bot_msg.delete()
        except Exception as e:
            logging.error("Upload failed: %s", e)
            self._bot_msg.edit_text(f"Upload failed! ❌\n\n`{e}`")

    def start(self):
        """Main entry point: check quota, download, upload."""
        try:
            if not check_quota(self._from_user):
                self._bot_msg.edit_text(
                    "You have exceeded your download quota. ❌\n\nPlease try again later."
                )
                return

            self._bot_msg.edit_text("Processing... ⏳")
            formats = self._setup_formats()
            self._record_usage()
            file_paths = self._download(formats)

            if not file_paths:
                self._bot_msg.edit_text("Download failed! ❌ No files received.")
                return

            from engine.helper import get_caption
            caption = get_caption(self._url, Path(file_paths[0]) if file_paths else None)
            self._upload(file_paths, caption)

        except Exception as e:
            logging.error("Download error: %s", e)
            self._bot_msg.edit_text(f"Error: ❌\n\n`{e}`")
