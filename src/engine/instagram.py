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

from database.model import check_quota
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
            "ignore_no_formats_error": True,
            "writethumbnail": True,
            "ignoreerrors": True,
            "js_runtimes": {"node": {}},
        }

        # Use cookies if present (helps with private/age-restricted content)
        cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt"))
        if not os.path.exists(cookie_path):
            cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "youtube-cookies.txt"))
        if not os.path.exists(cookie_path):
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
        except Exception as e:
            logging.warning("yt-dlp threw exception: %s. Proceeding to check for downloaded files anyway.", e)

        # Collect downloaded files (excluding the cookies file we injected)
        files = sorted(Path(self._tempdir.name).iterdir())
        valid_files = [str(f) for f in files if f.is_file() and f.name != "cookies.txt"]
        
        if not valid_files:
            self._bot_msg.edit_text("Instagram download failed! ❌\nNo media found.")
            return []

        return valid_files

    def start(self):
        try:
            if not check_quota(self._from_user):
                self._bot_msg.edit_text(
                    "You have exceeded your download quota. ❌\n\nPlease try again later."
                )
                return

            file_paths = self._download()
            if not file_paths:
                return

            self._record_usage()
            caption = f"📸 Instagram\n🔗 {self._url[:100]}"
            self._upload(file_paths, caption)
        except Exception as e:
            logging.error("Instagram error: %s", e)
            self._bot_msg.edit_text(f"Instagram download failed! ❌\n\n`{e}`")
        finally:
            try:
                self._tempdir.cleanup()
            except Exception as e:
                logging.warning("Tempdir cleanup failed: %s", e)
