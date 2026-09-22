"""Normalize and decode Mereani / Chen-style XSS strings before the oracle."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qsl, unquote_plus, urlsplit

_BR = re.compile(r"<br\s*/?>", re.I)
XSS_HINT = re.compile(
    r"(?is)<script|javascript:|onerror\s*=|onload\s*=|onmouseover\s*=|"
    r"onfocus\s*=|onclick\s*=|<svg|<iframe|<object|<embed|<math|"
    r"eval\s*\(|document\.cookie|fromcharcode|<img|<body\b|"
    r"srcdoc|settimeout\s*\(|expression\s*\("
)


def strip_br(payload: str) -> str:
    # Mereani CSV embeds literal <br> wraps. Do not strip real newlines:
    # mutations such as A14 rely on ASI after /drfv/\n.
    return _BR.sub("", payload)


def decode_loop(payload: str, rounds: int = 3) -> str:
    current = strip_br(payload)
    for _ in range(rounds):
        nxt = html.unescape(unquote_plus(current))
        if nxt == current:
            break
        current = nxt
    return current


def _query_values(decoded: str) -> list[str]:
    values: list[str] = []
    text = decoded
    if "://" not in text[:16] and "=" in text:
        text = "http://lab.local/?" + text
    try:
        parts = urlsplit(text)
    except ValueError:
        return values
    if parts.query:
        for _, value in parse_qsl(parts.query, keep_blank_values=True):
            if value:
                values.append(decode_loop(value))
    if parts.fragment:
        values.append(decode_loop(parts.fragment))
    return values


def injection_candidates(payload: str) -> list[str]:
    """HTML snippets to inject into the body. First hit that executes wins."""
    decoded = decode_loop(payload)
    out: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        item = item.strip()
        if not item or item in seen:
            return
        seen.add(item)
        out.append(item)

    add(decoded)
    add(strip_br(payload))
    for value in _query_values(decoded):
        add(value)
    return out
