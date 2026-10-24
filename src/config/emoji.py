# Raayan - emoji.py
# Centralized Custom & Standard Emoji Configuration

import itertools
import threading
from io import BytesIO

from pyrogram import raw, types
from pyrogram.raw.core import TLObject
from pyrogram.raw.core.primitives import Bytes, Int, Long, String

# Custom Emoji IDs provided by user
CUSTOM_DOWNLOADING_ID = 6096080291347042802
CUSTOM_SEARCHING_IDS = [
    5940510172089683697,
    5249245270381716113,
    5249245270381716113,
    5269518881818437964,
]

# Custom Emoji IDs for Inline Keyboard Buttons
BUTTON_VIDEO_ICON = 6010245481605632839
BUTTON_AUDIO_ICON = 5960715046869798071

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
    "pinterest": 5206525339517344010,          # 📌
    "x": None,                                 # 𝕏
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

    @classmethod
    def pinterest(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("pinterest"), "📌")

    @classmethod
    def x(cls) -> str:
        return make_emoji(CUSTOM_EMOJI_IDS.get("x"), "𝕏")


# ---- MTProto Layer Extension for Custom Emoji Inline Buttons ----

class KeyboardButtonStyle(TLObject):
    ID = 0x4fdd3430
    QUALNAME = "types.KeyboardButtonStyle"

    def __init__(self, icon: int = None):
        self.icon = icon

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))
        flags = (1 << 3) if self.icon else 0
        b.write(Int(flags))
        if self.icon:
            b.write(Long(self.icon))
        return b.getvalue()


class StyledKeyboardButtonCallback(TLObject):
    ID = 0xe62bc960
    QUALNAME = "types.KeyboardButtonCallback"

    def __init__(self, text: str, data: bytes, icon: int = None):
        self.text = text
        self.data = data
        self.icon = icon

    def write(self, *args) -> bytes:
        b = BytesIO()
        b.write(Int(self.ID, False))
        flags = (1 << 10) if self.icon else 0
        b.write(Int(flags))
        if self.icon:
            b.write(KeyboardButtonStyle(self.icon).write())
        b.write(String(self.text))
        b.write(Bytes(self.data))
        return b.getvalue()


_orig_btn_init = types.InlineKeyboardButton.__init__
_orig_btn_write = types.InlineKeyboardButton.write


def _custom_btn_init(self, text: str, *args, **kwargs):
    self.icon_custom_emoji_id = kwargs.pop("icon_custom_emoji_id", None)
    _orig_btn_init(self, text, *args, **kwargs)


async def _custom_btn_write(self, client):
    icon = getattr(self, "icon_custom_emoji_id", None)
    if self.callback_data is not None and icon:
        data = bytes(self.callback_data, "utf-8") if isinstance(self.callback_data, str) else self.callback_data
        return StyledKeyboardButtonCallback(text=self.text, data=data, icon=int(icon))
    return await _orig_btn_write(self, client)


types.InlineKeyboardButton.__init__ = _custom_btn_init
types.InlineKeyboardButton.write = _custom_btn_write
