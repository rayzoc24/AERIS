"""Input sanitisation (security check #7).

Strips control characters, null bytes, and obvious injection markers
from string payloads. HTML is sanitised server-side using a conservative
allowlist so citizen reports can render safely in the dashboard.
"""
from __future__ import annotations

import re
from typing import Any

import bleach

# Allow basic prose tags only. No scripts, no iframes, no inline styles.
_ALLOWED_TAGS = ["p", "br", "strong", "em", "ul", "ol", "li"]
_ALLOWED_ATTRS: dict[str, list[str]] = {}

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_DIACRITICS_NORMALISER = re.compile(r"[\u200B-\u200D\uFEFF]")


def sanitize_string(value: Any, max_length: int = 1024) -> str:
    """Strip control characters, BOM/zero-width chars, and collapse whitespace."""
    if value is None:
        return ""
    text = str(value)
    text = _CONTROL_CHARS.sub("", text)
    text = _DIACRITICS_NORMALISER.sub("", text)
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


def sanitize_html(value: Any, max_length: int = 4096) -> str:
    """Sanitise untrusted HTML, returning only allowlisted tags."""
    if value is None:
        return ""
    text = str(value)
    text = _CONTROL_CHARS.sub("", text)
    text = _DIACRITICS_NORMALISER.sub("", text)
    if len(text) > max_length:
        text = text[:max_length]
    return bleach.clean(text, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
