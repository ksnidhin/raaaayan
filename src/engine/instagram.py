#!/usr/bin/env python3
# coding: utf-8

# Raayan - instagram.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging
import time
import pathlib
import re

import filetype
import requests
from engine.base import BaseDownloader, generate_input_media


class InstagramDownload(BaseDownloader):
    def extract_code(self):
        patterns = [
            # Instagram stories highlights
            r"/stories/highlights/([a-zA-Z0-9_-]+)/",
            # Posts
            r"/p/([a-zA-Z0-9_-]+)/",
            # Reels
            r"/reel/([a-zA-Z0-9_-]+)/",
            # TV
            r"/tv/([a-zA-Z0-9_-]+)/",
            # Threads post (both with @username and without)
            r"(?:https?://)?(?:www\.)?(?:threads\.net)(?:/[@\w.]+)?(?:/post)?/([\w-]+)(?:/?\\?.*)?$",
        ]

        for pattern in patterns:
            match = re.search(pattern, self._url)
            if match:
                if pattern == patterns[0]:  # Check if it's the stories highlights pattern
                    # Return the URL as it is
                    return self._url
                else:
                    # Return the code part (first group)
                    return match.group(1)

        return None

    def _setup_formats(self) -> list | None:
        pass

    def _download(self, formats=None):
        try:
            resp = requests.get(f"http://instagram:15000/?url={self._url}").json()
        except Exception as e:
            self._bot_msg.edit_text(f"Download failed! ❌\n\n`{e}`")
            return []

        code = self.extract_code()
        counter = 1
        video_paths = []
        found_media_types = set()

        if not resp or not isinstance(resp, list):
            self._bot_msg.edit_text("Instagram download failed: empty response ❌")
            return []

        for media_url in resp:
            try:
                r = requests.get(media_url, timeout=60)
                r.raise_for_status()
                ext = "mp4" if "video" in r.headers.get("content-type", "") else "jpg"
                filename = pathlib.Path(self._tempdir.name) / f"{code}_{counter}.{ext}"
                with open(filename, "wb") as f:
                    f.write(r.content)
                guessed_ext = filetype.guess_extension(filename)
                if guessed_ext:
                    new_name = filename.with_suffix(f".{guessed_ext}")
                    filename.rename(new_name)
                    video_paths.append(str(new_name))
                else:
                    video_paths.append(str(filename))
                counter += 1
            except Exception as e:
                logging.warning("Failed to download Instagram media item: %s", e)

        return video_paths

    def start(self):
        try:
            self._bot_msg.edit_text("Downloading from Instagram... ⏳")
            file_paths = self._download()

            if not file_paths:
                return

            from engine.helper import get_caption
            caption = f"📸 Instagram\n🔗 {self._url}"
            self._upload(file_paths, caption)
        except Exception as e:
            logging.error("Instagram download error: %s", e)
            self._bot_msg.edit_text(f"Instagram download failed! ❌\n\n`{e}`")
