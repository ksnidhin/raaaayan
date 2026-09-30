#!/usr/bin/env python3
# coding: utf-8

# Raayan - krakenfiles.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: SanujaNS <sanujas@sanuja.biz>
# License: Apache 2.0

import requests
from bs4 import BeautifulSoup
from engine.direct import DirectDownload


def krakenfiles_download(client, bot_message, url: str):
    session = requests.Session()

    def _extract_form_data(url: str) -> tuple[str, dict]:
        try:
            resp = session.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            form = soup.find("form", {"id": "dl-form"})
            if not form:
                raise ValueError("ERROR: Unable to find download form.")

            post_url = form.get("action")
            if not post_url:
                raise ValueError("ERROR: Unable to find post link.")
            post_url = f"https://krakenfiles.com{post_url}"

            token_input = soup.find("input", {"id": "dl-token"})
            if not token_input:
                raise ValueError("ERROR: Unable to find download token.")
            data = {"token": token_input.get("value", "")}

            return post_url, data
        except Exception as e:
            raise ValueError(f"KrakenFiles extraction failed: {e}")

    try:
        bot_message.edit_text("Extracting KrakenFiles link... ⏳")
        post_url, form_data = _extract_form_data(url)

        resp = session.post(post_url, data=form_data)
        resp.raise_for_status()
        json_resp = resp.json()
        direct_url = json_resp.get("url")

        if not direct_url:
            raise ValueError("No download URL in KrakenFiles response")

        dl = DirectDownload(client, bot_message, direct_url)
        dl.start()

    except Exception as e:
        bot_message.edit_text(f"KrakenFiles download failed! ❌\n\n`{e}`")
