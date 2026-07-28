"""
utils/formatting.py
====================
Small display-formatting helpers shared across pages.
"""

from datetime import timedelta


def format_elapsed(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    h, rem = divmod(td.seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_frame_progress(current: int, total: int) -> str:
    return f"{current} / {total if total else '?'}"


def safe_pct(current: int, total: int) -> int:
    if not total:
        return 0
    return int(min(100, (current / total) * 100))
