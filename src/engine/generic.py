#!/usr/bin/env python3
# coding: utf-8

# Raayan - generic.py (yt-dlp / YouTube engine)
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging
import os
from pathlib import Path

import yt_dlp

from config import AUDIO_FORMAT
from utils import is_youtube
from database.model import get_format_settings, get_quality_settings
from engine.base import BaseDownloader


def match_filter(info_dict):
    if info_dict.get("is_live"):
        raise NotImplementedError("Skipping live video")
    return None  # Allow download for non-live videos


class YoutubeDownload(BaseDownloader):
    @staticmethod
    def get_format(m):
        return [
            f"bestvideo[ext=mp4][height={m}]+bestaudio[ext=m4a]",
            f"bestvideo[vcodec^=avc][height={m}]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]/best",
        ]

    def _setup_formats(self) -> list | None:
        if not is_youtube(self._url):
            return [None]

        quality, format_ = get_quality_settings(self._chat_id), get_format_settings(self._chat_id)
        # quality: high, medium, low, custom
        # format: audio, video, document
        formats = []
        defaults = [
            # webm, vp9 and av01 are not streamable on telegram, so we'll extract only mp4
            "bestvideo[ext=mp4][vcodec!*=av01][vcodec!*=vp09]+bestaudio[ext=m4a]/bestvideo+bestaudio",
            "bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]/best",
            None,
        ]
        audio = AUDIO_FORMAT or "m4a"
        maps = {
            "high-audio": [f"bestaudio[ext={audio}]"],
            "high-video": defaults,
            "high-document": defaults,
            "medium-audio": [f"bestaudio[ext={audio}]"],  # no medium audio :-(
            "medium-video": self.get_format(720),
            "medium-document": self.get_format(720),
            "low-audio": [f"bestaudio[ext={audio}]"],
            "low-video": self.get_format(480),
            "low-document": self.get_format(480),
            "custom-audio": [],
            "custom-video": [],
            "custom-document": [],
        }

        key = f"{quality}-{format_}"
        formats = maps.get(key, defaults)
        return formats

    def _download(self, formats=None):
        file_paths = []
        errors = []

        format_list = formats if formats else [None]

        for fmt in format_list:
            ydl_opts = {
                "outtmpl": str(Path(self._tempdir.name) / "%(title)s.%(ext)s"),
                "progress_hooks": [self.download_hook],
                "match_filter": match_filter,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }

            if fmt:
                ydl_opts["format"] = fmt

            # Merge audio/video if format string has '+' and ffmpeg is available
            from config import ENABLE_FFMPEG
            if ENABLE_FFMPEG:
                ydl_opts["merge_output_format"] = "mp4"

            # Use cookies if present
            cookie_path = "/app/youtube-cookies.txt"
            if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
                import shutil
                temp_cookie_path = str(Path(self._tempdir.name) / "cookies.txt")
                shutil.copy2(cookie_path, temp_cookie_path)
                ydl_opts["cookiefile"] = temp_cookie_path

            try:
                self._bot_msg.edit_text(f"Downloading... ⏳")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self._url, download=True)
                    if info:
                        filename = ydl.prepare_filename(info)
                        if os.path.exists(filename):
                            file_paths.append(filename)
                        else:
                            # Try to find any file in tempdir
                            found = list(Path(self._tempdir.name).iterdir())
                            if found:
                                file_paths = [str(f) for f in found]
                break  # Success on first working format
            except Exception as e:
                logging.warning("Format %s failed: %s", fmt, e)
                errors.append(str(e))
                continue

        if not file_paths:
            err_msg = "\n".join(errors[:2])
            raise Exception(f"All formats failed:\n{err_msg}")

        return file_paths
