# Raayan - x.py
# Engine for X (formerly Twitter) Posts (Videos, GIFs, Photos)

import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
import yt_dlp

from config import Emoji
from database.model import check_quota
from engine.base import BaseDownloader


class XDownload(BaseDownloader):

    def _setup_formats(self) -> list | None:
        return [None]

    def _resolve_url(self, url: str) -> str:
        """Resolve shortlinks (like t.co) to canonical x.com/twitter.com URL."""
        try:
            resp = requests.get(
                url,
                allow_redirects=True,
                timeout=10,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            return resp.url
        except Exception as e:
            logging.warning("Error resolving X URL: %s", e)
            return url

    def _download(self, formats=None) -> list[str]:
        canonical_url = self._resolve_url(self._url)
        logging.info("Downloading X content from: %s", canonical_url)

        self._bot_msg.edit_text(f"Downloading from X... {Emoji.downloading()}")

        # 1. Primary extraction via yt-dlp
        cookie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cookies.txt"))
        if not os.path.exists(cookie_path):
            cookie_path = "/app/youtube-cookies.txt"

        ydl_opts = {
            "outtmpl": str(Path(self._tempdir.name) / "%(title)s.%(ext)s"),
            "progress_hooks": [self.download_hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "js_runtimes": {"node": {}},
        }
        if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
            ydl_opts["cookiefile"] = cookie_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(canonical_url, download=True)
                if info:
                    fn = ydl.prepare_filename(info)
                    if os.path.exists(fn):
                        return [fn]
        except Exception as e:
            logging.info("yt-dlp X extraction failed: %s", e)

        # Check if yt-dlp downloaded any file into tempdir
        found = [
            str(f) for f in Path(self._tempdir.name).iterdir()
            if f.is_file() and f.name != "cookies.txt"
        ]
        if found:
            return found

        # 2. Fallback via public syndication/API (handles images and guest-token issues)
        match = re.search(r'/(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)', canonical_url)
        if match:
            username, status_id = match.group(1), match.group(2)
            for api_host in ["api.fxtwitter.com", "api.vxtwitter.com"]:
                try:
                    api_url = f"https://{api_host}/{username}/status/{status_id}"
                    resp = requests.get(api_url, timeout=12, headers={"User-Agent": "RaayanBot/1.0"})
                    if resp.status_code == 200:
                        data = resp.json()
                        tweet = data.get("tweet", {})
                        media = tweet.get("media", {})

                        # Check videos
                        videos = media.get("videos", [])
                        if videos:
                            best_video = max(videos, key=lambda v: v.get("bitrate", 0)) if "bitrate" in videos[0] else videos[0]
                            vid_url = best_video.get("url")
                            if vid_url:
                                out_p = Path(self._tempdir.name) / f"x_{status_id}.mp4"
                                with requests.get(vid_url, stream=True, timeout=20) as r:
                                    r.raise_for_status()
                                    with open(out_p, "wb") as f:
                                        for chunk in r.iter_content(chunk_size=16384):
                                            f.write(chunk)
                                return [str(out_p)]

                        # Check photos
                        photos = media.get("photos", [])
                        if photos:
                            downloaded = []
                            for idx, p in enumerate(photos):
                                p_url = p.get("url")
                                if p_url:
                                    ext = p_url.split(".")[-1].split("?")[0].lower()
                                    if ext not in ["jpg", "jpeg", "png", "webp"]:
                                        ext = "jpg"
                                    out_p = Path(self._tempdir.name) / f"x_{status_id}_{idx}.{ext}"
                                    with requests.get(p_url, stream=True, timeout=20) as r:
                                        r.raise_for_status()
                                        with open(out_p, "wb") as f:
                                            for chunk in r.iter_content(chunk_size=16384):
                                                f.write(chunk)
                                    downloaded.append(str(out_p))
                            if downloaded:
                                return downloaded

                except Exception as ex:
                    logging.warning("X API fallback error (%s): %s", api_host, ex)

        self._bot_msg.edit_text(f"X download failed! {Emoji.error()}\nNo media found or post is private.")
        return []

    def start(self):
        try:
            if not check_quota(self._from_user):
                self._bot_msg.edit_text(
                    f"You have exceeded your download quota. {Emoji.error()}\n\nPlease try again later."
                )
                return

            file_paths = self._download()
            if not file_paths:
                return

            self._record_usage()
            caption = f"{Emoji.x()} X\n{Emoji.link()} {self._url[:100]}"
            self._upload(file_paths, caption)
        except Exception as e:
            import html as html_lib
            logging.error("X download error: %s", e)
            self._bot_msg.edit_text(f"X download failed! {Emoji.error()}\n\n<code>{html_lib.escape(str(e))}</code>")
        finally:
            try:
                self._tempdir.cleanup()
            except Exception as e:
                logging.warning("Tempdir cleanup failed: %s", e)
