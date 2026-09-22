"""Chen/Pasini Table 2 actions, written so payloads can still execute.

Pasini artifact bugs we do not copy:
- A1 replaced the whole javascript match
- A18 was a no-op
- A20 was a stub
- A21/A22/A27 substituted `alert` with an expression that already contains `(1)`,
  turning `alert(1)` into `...(1)(1)`
"""

from __future__ import annotations

import base64
import random
import re
from collections.abc import Callable

JS_WORD = re.compile(
    r"(?i)j(?:\s|&[#\w]+;)*a(?:\s|&[#\w]+;)*v(?:\s|&[#\w]+;)*a"
    r"(?:\s|&[#\w]+;)*s(?:\s|&[#\w]+;)*c(?:\s|&[#\w]+;)*r"
    r"(?:\s|&[#\w]+;)*i(?:\s|&[#\w]+;)*p(?:\s|&[#\w]+;)*t"
)
HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^>]*)?>")
OPEN_TAG = re.compile(r"<[A-Za-z][A-Za-z0-9]*(?:\s[^>]*)?>")
ATTR_NAME = re.compile(r"([A-Za-z_:][\w:.-]*)(\s*=)")
SCRIPT_OPEN = re.compile(r"<script\b[^>]*>", re.I)
VOID_TAG = re.compile(
    r"<(?:area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr)\b[^>]*>",
    re.I,
)
JS_CALL = re.compile(r"\b([\w$.]+)\(")
ALERT = re.compile(r"\balert\b")
HTTP = re.compile(r"https?://", re.I)
DATA_PROTO = re.compile(r"data:", re.I)


def _rng(rng: random.Random | None) -> random.Random:
    return rng if rng is not None else random.Random(0)


def _mix_case(text: str, rng: random.Random) -> str:
    return "".join(rng.choice((ch.lower(), ch.upper())) if ch.isalpha() else ch for ch in text)


def _inject_js_word(payload: str, token: str) -> str:
    def inject(match: re.Match[str]) -> str:
        word = match.group(0)
        mid = max(1, len(word) // 2)
        return word[:mid] + token + word[mid:]

    if not JS_WORD.search(payload):
        return payload
    return JS_WORD.sub(inject, payload, count=1)


def _has_javascript(payload: str) -> bool:
    return bool(JS_WORD.search(payload) or SCRIPT_OPEN.search(payload))


def _encode_calls(payload: str, fmt) -> str:
    if not _has_javascript(payload):
        return payload

    def enc(match: re.Match[str]) -> str:
        return "".join(fmt(ch) for ch in match.group(1)) + "("

    return JS_CALL.sub(enc, payload)


def action_1(payload: str, rng: random.Random | None = None) -> str:
    """A1: insert &#14 before javascript (keep the original word)."""
    if not JS_WORD.search(payload):
        return payload
    return JS_WORD.sub(lambda m: "&#14" + m.group(0), payload, count=1)


def action_2(payload: str, rng: random.Random | None = None) -> str:
    """A2: mixed-case HTML attribute names."""
    rng = _rng(rng)

    def mix_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        return ATTR_NAME.sub(lambda m: _mix_case(m.group(1), rng) + m.group(2), tag)

    return OPEN_TAG.sub(mix_tag, payload)


def action_3(payload: str, rng: random.Random | None = None) -> str:
    """A3: replace spaces with /, %0A or %0D."""
    repl = _rng(rng).choice(["/", "%0A", "%0D"])
    return payload.replace(" ", repl)


def action_4(payload: str, rng: random.Random | None = None) -> str:
    """A4: mixed-case HTML tag names."""
    rng = _rng(rng)

    def mix(match: re.Match[str]) -> str:
        return _mix_case(match.group(0), rng)

    return HTML_TAG.sub(mix, payload)


def action_5(payload: str, rng: random.Random | None = None) -> str:
    """A5: drop the closing '>' of a void/single tag."""
    match = VOID_TAG.search(payload)
    if not match:
        return payload
    tag = match.group(0)
    if tag.endswith(">"):
        return payload[: match.start()] + tag[:-1] + " " + payload[match.end() :]
    return payload


def action_6(payload: str, rng: random.Random | None = None) -> str:
    return _inject_js_word(payload, "&NewLine;")


def action_7(payload: str, rng: random.Random | None = None) -> str:
    return _inject_js_word(payload, "&#x09;")


def action_8(payload: str, rng: random.Random | None = None) -> str:
    return _encode_calls(payload, lambda ch: f"&#x{ord(ch):x};")


def action_9(payload: str, rng: random.Random | None = None) -> str:
    """A9: double the first HTML tag."""
    match = HTML_TAG.search(payload)
    if not match:
        return payload
    tag = match.group(0)
    return payload[: match.start()] + tag + tag + payload[match.end() :]


def action_10(payload: str, rng: random.Random | None = None) -> str:
    return HTTP.sub("//", payload)


def action_11(payload: str, rng: random.Random | None = None) -> str:
    return _encode_calls(payload, lambda ch: f"&#{ord(ch)};")


def action_12(payload: str, rng: random.Random | None = None) -> str:
    return _inject_js_word(payload, "&colon;")


def action_13(payload: str, rng: random.Random | None = None) -> str:
    return _inject_js_word(payload, "&Tab;")


def action_14(payload: str, rng: random.Random | None = None) -> str:
    if not SCRIPT_OPEN.search(payload):
        return payload
    return SCRIPT_OPEN.sub("<script>/drfv/\n", payload, count=1)


def action_15(payload: str, rng: random.Random | None = None) -> str:
    return payload.replace("(", "`").replace(")", "`")


def action_16(payload: str, rng: random.Random | None = None) -> str:
    match = DATA_PROTO.search(payload)
    if not match:
        return payload
    head, tail = payload[: match.end()], payload[match.end() :]
    encoded = base64.b64encode(tail.encode("utf-8", "surrogateescape")).decode("ascii")
    return head + encoded


def action_17(payload: str, rng: random.Random | None = None) -> str:
    return payload.replace('"', "").replace("'", "")


def action_18(payload: str, rng: random.Random | None = None) -> str:
    """A18: Unicode-escape JS identifiers in calls. Pasini code was a no-op."""
    return _encode_calls(payload, lambda ch: f"\\u{ord(ch):04x}")


def action_19(payload: str, rng: random.Random | None = None) -> str:
    encoded = "&#x6A;&#x61;&#x76;&#x61;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;"
    if not JS_WORD.search(payload):
        return payload
    return JS_WORD.sub(encoded, payload, count=1)


def action_20(payload: str, rng: random.Random | None = None) -> str:
    """A20: replace '>' of a void tag with '<'. Pasini code was a stub."""
    match = VOID_TAG.search(payload)
    if not match:
        return payload
    tag = match.group(0)
    if tag.endswith(">"):
        return payload[: match.start()] + tag[:-1] + "<" + payload[match.end() :]
    return payload


def action_21(payload: str, rng: random.Random | None = None) -> str:
    """A21: alert → top['al'+'ert']  (does not append extra (1))."""
    return ALERT.sub("top['al'+'ert']", payload)


def action_22(payload: str, rng: random.Random | None = None) -> str:
    """A22: alert → top[8680439..toString(30)]"""
    return ALERT.sub("top[8680439..toString(30)]", payload)


def action_23(payload: str, rng: random.Random | None = None) -> str:
    noise = "search?q=ok "
    match = HTML_TAG.search(payload)
    if match:
        return payload[: match.start()] + noise + payload[match.start() :]
    return noise + payload


def action_24(payload: str, rng: random.Random | None = None) -> str:
    def comment(match: re.Match[str]) -> str:
        tag = match.group(0)
        if tag.endswith(">"):
            return tag[:-1] + " <!--x-->" + ">"
        return tag + " <!--x-->"

    return HTML_TAG.sub(comment, payload, count=1)


def action_25(payload: str, rng: random.Random | None = None) -> str:
    if not JS_WORD.search(payload):
        return payload
    return JS_WORD.sub("vbscript", payload, count=1)


def action_26(payload: str, rng: random.Random | None = None) -> str:
    rng = _rng(rng)

    def inject(match: re.Match[str]) -> str:
        tag = match.group(0)
        slots = [i for i, ch in enumerate(tag) if ch in " <>"]
        if not slots:
            return tag
        pos = rng.choice(slots)
        return tag[:pos] + "%00" + tag[pos:]

    return HTML_TAG.sub(inject, payload, count=1)


def action_27(payload: str, rng: random.Random | None = None) -> str:
    """A27: alert → top[/al/.source+/ert/.source]"""
    return ALERT.sub("top[/al/.source+/ert/.source]", payload)


ACTIONS: dict[int, Callable[..., str]] = {
    1: action_1,
    2: action_2,
    3: action_3,
    4: action_4,
    5: action_5,
    6: action_6,
    7: action_7,
    8: action_8,
    9: action_9,
    10: action_10,
    11: action_11,
    12: action_12,
    13: action_13,
    14: action_14,
    15: action_15,
    16: action_16,
    17: action_17,
    18: action_18,
    19: action_19,
    20: action_20,
    21: action_21,
    22: action_22,
    23: action_23,
    24: action_24,
    25: action_25,
    26: action_26,
    27: action_27,
}

ACTION_META = {
    1: {"name": "A1", "paper": 'Add "&#14" before "javascript"', "group": "javascript-entity"},
    2: {"name": "A2", "paper": "Mixed case HTML attributes", "group": "html-case"},
    3: {"name": "A3", "paper": 'Replace spaces with "/", "%0A" or "%0D"', "group": "whitespace"},
    4: {"name": "A4", "paper": "Mixed case HTML tags", "group": "html-case"},
    5: {"name": "A5", "paper": "Remove closing symbol of single tags", "group": "html-tag"},
    6: {"name": "A6", "paper": 'Add "&NewLine;" to javascript', "group": "javascript-entity"},
    7: {"name": "A7", "paper": 'Add "&#x09" to javascript', "group": "javascript-entity"},
    8: {"name": "A8", "paper": "HTML entity encoding for JS (hex)", "group": "js-encode"},
    9: {"name": "A9", "paper": "Double write HTML tags", "group": "html-tag"},
    10: {"name": "A10", "paper": 'Replace "http://" with "//"', "group": "url"},
    11: {"name": "A11", "paper": "HTML entity encoding for JS (decimal)", "group": "js-encode"},
    12: {"name": "A12", "paper": 'Add "&colon;" to javascript', "group": "javascript-entity"},
    13: {"name": "A13", "paper": 'Add "&Tab;" to javascript', "group": "javascript-entity"},
    14: {"name": "A14", "paper": 'Add "/drfv/" after script tag', "group": "html-tag"},
    15: {"name": "A15", "paper": "Replace () with backticks", "group": "js-syntax"},
    16: {"name": "A16", "paper": "Base64-encode data: protocol", "group": "url"},
    17: {"name": "A17", "paper": "Remove quotation marks", "group": "html-tag"},
    18: {"name": "A18", "paper": "Unicode encoding for JS code", "group": "js-encode"},
    19: {"name": "A19", "paper": "HTML entity encoding for javascript", "group": "javascript-entity"},
    20: {"name": "A20", "paper": 'Replace ">" of single label with "<"', "group": "html-tag"},
    21: {"name": "A21", "paper": "alert via string concat", "group": "alert"},
    22: {"name": "A22", "paper": "alert via toString(30)", "group": "alert"},
    23: {"name": "A23", "paper": "Interference string before payload", "group": "noise"},
    24: {"name": "A24", "paper": "Comment inside tags", "group": "html-tag"},
    25: {"name": "A25", "paper": "vbscript replaces javascript", "group": "legacy"},
    26: {"name": "A26", "paper": "Inject %00 into tags", "group": "legacy"},
    27: {"name": "A27", "paper": "alert via regex .source", "group": "alert"},
}


def apply_action(action_id: int, payload: str, rng: random.Random | None = None) -> str:
    if action_id not in ACTIONS:
        raise KeyError(f"unknown action {action_id}")
    return ACTIONS[action_id](payload, rng=rng)
