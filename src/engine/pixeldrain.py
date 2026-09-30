#!/usr/bin/env python3
# coding: utf-8

# Raayan - pixeldrain.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: SanujaNS <sanujas@sanuja.biz>
# License: Apache 2.0

import tempfile
import pathlib
import re
from urllib.parse import urlparse
from engine.direct import DirectDownload


def pixeldrain_download(client, bot_message, url):
    FILE_URL_FORMAT = "https://pixeldrain.com/api/file/{}?download"
    USER_PAGE_PATTERN = re.compile(r"https://pixeldrain.com/u/(\w+)")

    def _extract_file_id(url):
        if match := USER_PAGE_PATTERN.match(url):
            return match.group(1)

        parsed = urlparse(url)
        if parsed.path.startswith("/file/"):
            return parsed.path.split("/")[-1]

        return None

    file_id = _extract_file_id(url)
    if not file_id:
        bot_message.edit_text("Could not extract file ID from Pixeldrain URL ❌")
        return

    direct_url = FILE_URL_FORMAT.format(file_id)
    dl = DirectDownload(client, bot_message, direct_url)
    dl.start()
