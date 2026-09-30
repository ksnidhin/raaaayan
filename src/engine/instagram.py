#!/usr/bin/env python3
# coding: utf-8

# Raayan - instagram.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0
#
# CHANGE from upstream: Instagram now downloads via yt-dlp directly instead of
# calling the sidecar service at http://instagram:15000 (which is not deployed).
# REASON: Sidecar service not available. yt-dlp natively supports Instagram
#         posts, reels, stories, and carousels.
# EVIDENCE: yt-dlp supported sites list includes instagram.com

import logging
import os
from pathlib import Path

import yt_dlp

from engine.base import BaseDownloader


class InstagramDownload(BaseDownloader):

    def _setup_formats(self) -> list | None:
        # Instagram: always download best available, no format selection needed
        return [None]

    def _download(self, formats=None):
        ydl_opts = {
            "outtmpl": str(Path(self._tempdir.name) / "%(id)s.%(ext)s"),
            "progress_hooks": [self.download_hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,   # allow carousels/albums
            "extract_flat": False,
        }

        # Use cookies if present (helps with private/age-restricted content)
        cookie_path = "/app/youtube-cookies.txt"
        if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
            import shutil
            temp_cookie_path = str(Path(self._tempdir.name) / "cookies.txt")
            shutil.copy2(cookie_path, temp_cookie_path)
            ydl_opts["cookiefile"] = temp_cookie_path

        try:
            self._bot_msg.edit_text("Downloading from Instagram... ⏳")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self._url, download=True)

            # Collect downloaded files
            files = sorted(Path(self._tempdir.name).iterdir())
            if not files:
                raise Exception("yt-dlp completed but no files were saved")

            return [str(f) for f in files if f.is_file()]

        except Exception as e:
            logging.error("Instagram yt-dlp download failed: %s", e)
            self._bot_msg.edit_text(f"Instagram download failed! ❌\n\n`{e}`")
            return []

    def start(self):
        try:
            file_paths = self._download()
            if not file_paths:
                return

            caption = f"📸 Instagram\n🔗 {self._url[:100]}"
            self._upload(file_paths, caption)
        except Exception as e:
            logging.error("Instagram error: %s", e)
            self._bot_msg.edit_text(f"Instagram download failed! ❌\n\n`{e}`")
