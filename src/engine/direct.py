#!/usr/bin/env python3
# coding: utf-8

# Raayan - direct.py (direct download engine: requests + aria2)
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging
import os
import re
import pathlib
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import filetype
import requests

from config import ENABLE_ARIA2, TMPFILE_PATH
from engine.base import BaseDownloader


class DirectDownload(BaseDownloader):

    def _setup_formats(self) -> list | None:
        # direct download doesn't need to setup formats
        pass

    def _requests_download(self):
        logging.info("Requests download with url %s", self._url)
        response = requests.get(self._url, stream=True)
        response.raise_for_status()
        file = Path(self._tempdir.name).joinpath(uuid4().hex)
        with open(file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        ext = filetype.guess_extension(file)
        if ext is not None:
            new_name = file.with_suffix(f".{ext}")
            file.rename(new_name)
            return [new_name.as_posix()]

        return [file.as_posix()]

    def _aria2_download(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        self._process = None
        try:
            self._bot_msg.edit_text("Aria2 download starting...")
            temp_dir = self._tempdir.name
            command = [
                "aria2c",
                "--max-tries=3",
                "--max-concurrent-downloads=8",
                "--max-connection-per-server=16",
                "--split=16",
                "--summary-interval=1",
                "--console-log-level=error",
                f"--user-agent={ua}",
                f"--dir={temp_dir}",
                self._url,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if result.returncode != 0:
                raise Exception(f"aria2c exited with code {result.returncode}: {result.stderr}")

            # Find downloaded file(s)
            files = list(Path(temp_dir).iterdir())
            if not files:
                raise Exception("aria2c completed but no files found")

            return [str(f) for f in files]

        except subprocess.TimeoutExpired:
            raise Exception("aria2c download timed out")

    def _download(self, formats=None):
        if ENABLE_ARIA2:
            try:
                return self._aria2_download()
            except Exception as e:
                logging.warning("aria2 failed, falling back to requests: %s", e)

        return self._requests_download()
