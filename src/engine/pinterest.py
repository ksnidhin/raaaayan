# Raayan - pinterest.py
# Engine for Pinterest Pins (Photos, Videos, GIFs)

import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import filetype
import requests
import yt_dlp
from bs4 import BeautifulSoup

from config import Emoji
from database.model import check_quota
from engine.base import BaseDownloader


class PinterestDownload(BaseDownloader):

    def _setup_formats(self) -> list | None:
        return [None]

    def _resolve_url(self, url: str) -> str:
        """Follow redirects (e.g. pin.it shortlinks) to get the canonical Pinterest URL."""
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
            logging.warning("Error resolving Pinterest URL: %s", e)
            return url

    def _download(self, formats=None) -> list[str]:
        file_paths = []
        canonical_url = self._resolve_url(self._url)
        logging.info("Downloading Pinterest content from: %s", canonical_url)

        # 1. First attempt with yt-dlp (in case it is a video pin)
        try:
            self._bot_msg.edit_text(f"Downloading from Pinterest... {Emoji.downloading()}")
            ydl_opts = {
                "outtmpl": str(Path(self._tempdir.name) / "%(title)s.%(ext)s"),
                "progress_hooks": [self.download_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "js_runtimes": {"node": {}},
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(canonical_url, download=True)
                if info:
                    fn = ydl.prepare_filename(info)
                    if os.path.exists(fn):
                        file_paths.append(fn)
        except Exception as e:
            logging.info("yt-dlp video extraction skipped or failed (likely an image pin): %s", e)

        # Check if yt-dlp downloaded anything
        found = [
            str(f) for f in Path(self._tempdir.name).iterdir()
            if f.is_file() and f.name != "cookies.txt"
        ]
        if found:
            return found

        # 2. Scrape Pinterest page directly for high-resolution images or videos
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })

        try:
            resp = session.get(canonical_url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Check for video in meta or regex
            og_video = soup.find("meta", property="og:video") or soup.find("meta", property="og:video:secure_url")
            video_url = og_video["content"] if og_video else None
            if not video_url:
                v_match = re.search(r'https://v\.pinimg\.com/[^\s"\'<>]+\.mp4', resp.text)
                if v_match:
                    video_url = v_match.group(0)

            if video_url:
                out_path = Path(self._tempdir.name) / "pinterest_video.mp4"
                r = session.get(video_url, stream=True, timeout=20)
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=16384):
                        f.write(chunk)
                return [str(out_path)]

            # If no video, look for images
            image_candidates = []
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                image_candidates.append(og_image["content"])

            for m in re.finditer(r'https://i\.pinimg\.com/[^\s"\'<>]+\.(?:jpg|png|webp|gif)', resp.text):
                image_candidates.append(m.group(0))

            if not image_candidates:
                self._bot_msg.edit_text(f"Pinterest download failed! {Emoji.error()}\nNo media found.")
                return []

            best_img_url = None
            for cand in image_candidates:
                orig = re.sub(r'https://i\.pinimg\.com/\d+x\d*/', 'https://i.pinimg.com/originals/', cand)
                orig = re.sub(r'https://i\.pinimg\.com/\d+x/', 'https://i.pinimg.com/originals/', orig)
                try:
                    h = session.head(orig, timeout=5)
                    if h.status_code == 200:
                        best_img_url = orig
                        break
                except Exception:
                    pass
                if not best_img_url and cand.startswith("http"):
                    best_img_url = cand

            if not best_img_url:
                best_img_url = image_candidates[0]

            ext = best_img_url.split(".")[-1].split("?")[0].lower()
            if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
                ext = "jpg"
            out_path = Path(self._tempdir.name) / f"pinterest_{Path(self._tempdir.name).name}.{ext}"

            r = session.get(best_img_url, stream=True, timeout=20)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    f.write(chunk)

            return [str(out_path)]

        except Exception as e:
            logging.error("Pinterest scraping failed: %s", e)
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
            caption = f"{Emoji.pinterest()} Pinterest\n{Emoji.link()} {self._url[:100]}"
            self._upload(file_paths, caption)
        except Exception as e:
            import html as html_lib
            logging.error("Pinterest error: %s", e)
            self._bot_msg.edit_text(f"Pinterest download failed! {Emoji.error()}\n\n<code>{html_lib.escape(str(e))}</code>")
        finally:
            try:
                self._tempdir.cleanup()
            except Exception as e:
                logging.warning("Tempdir cleanup failed: %s", e)
