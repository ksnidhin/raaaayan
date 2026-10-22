# Raayan - emoji.py
# Centralized Custom & Standard Emoji Configuration

import itertools
import threading

# Custom Emoji IDs provided by user
CUSTOM_DOWNLOADING_ID = 6096080291347042802
CUSTOM_SEARCHING_IDS = [
    5940510172089683697,
    5249245270381716113,
    5249245270381716113,
    5269518881818437964,
]

# Map for custom emojis provided by user
CUSTOM_EMOJI_IDS = {
    "error": 5199519380274176771,              # ❌
    "uploading": 5258043150110301407,          # 📤
    "success": 5424998570539373838,            # ✅
    "clapper": 5318881915908928251,            # 🎬
    "instagram": 5474348994605891991,          # 📸
    "package": 5294340837851802907,            # 📦
    "settings": 5832572966721818453,           # 🎚
    "stopwatch": 5262540380301191210,          # ⏱
    "link": 5246708069991205241,               # 🔗
    "ping": 5269563867305879894,               # 🏓
}


def make_emoji(emoji_id: int | None, fallback: str) -> str:
    """Format custom emoji for Pyrogram HTML parser with fallback."""
    if emoji_id:
        return f'<emoji id="{emoji_id}">{fallback}</emoji>'
    return fallback


class Emoji:
    """Provides custom or fallback emojis for bot replies."""

    DOWNLOADING = make_emoji(CUSTOM_DOWNLOADING_ID, "⏳")

    # Sequence of searching emojis (used one by one)
    SEARCH_FRAMES = [make_emoji(eid, "🔍") for eid in CUSTOM_SEARCHING_IDS]
    _search_cycle = itertools.cycle(SEARCH_FRAMES)
    _lock = threading.Lock()

    @classmethod
    def get_search_emoji(cls, step: int | None = None) -> str:
        """Return the next searching emoji frame in sequence."""
        if step is not None:
            return cls.SEARCH_FRAMES[step % len(cls.SEARCH_FRAMES)]
        with cls._lock:
            return next(cls._search_cycle)

    @classmethod
    def downloading(cls) -> str:
        return cls.DOWNLOADING

    @classmethod
    def error(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("error"), "❌")

    @classmethod
    def uploading(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("uploading"), "📤")

    @classmethod
    def success(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("success"), "✅")

    @classmethod
    def clapper(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("clapper"), "🎬")

    @classmethod
    def instagram(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("instagram"), "📸")

    @classmethod
    def package(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("package"), "📦")

    @classmethod
    def settings(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("settings"), "🎚")

    @classmethod
    def stopwatch(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("stopwatch"), "⏱")

    @classmethod
    def link(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("link"), "🔗")

    @classmethod
    def ping(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("ping"), "🏓")
