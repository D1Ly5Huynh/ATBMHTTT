"""Chen/Pasini detector preprocess: lowercase, unescape, 10% vocab, None=OOV."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote_plus, urlsplit, urlunsplit

import numpy as np
import torch

TOKEN_RE = re.compile(
    r"(?x)"
    r"[\w\.]+?\("
    r"|\"[^\"]*?\""
    r"|'[^']*?'"
    r"|http://\w+"
    r"|</\w+>"
    r"|<.+?>"
    r"|\b\w+="
    r"|\w+:"
    r"|(?<=\()\S+(?=\))"
    r"|\)|>"
)
BR_RE = re.compile(r"<br\s*/?>", re.I)
MAX_LENGTH = 40  # paper 200; median tokens=6. 40 keeps protocol, trains on CPU.
PAD_TOKEN = "<pad>"
OOV_TOKEN = "None"


def preprocess_one(payload: str) -> str:
    text = str(payload).lower()
    if "=" in text:
        prefix = text.split("=", 1)[0]
        text = text.replace(prefix, "http://u")
    elif text.startswith("http://") or text.startswith("https://"):
        parts = list(urlsplit(text))
        parts[0] = "http"
        parts[1] = "u"
        text = urlunsplit(parts)
    text = html.unescape(text)
    text = BR_RE.sub("", text)
    text = unquote_plus(text)
    text = re.sub(r"\\+", "", text)
    text = re.sub(r"(?<!%)\d", "0", text)
    text = re.sub(r"0+", "0", text)
    return text


def tokenize(payload: str) -> list[str]:
    return TOKEN_RE.findall(preprocess_one(payload))


def build_vocab(payloads: list[str], keep_ratio: float = 0.1) -> list[str]:
    counts: Counter[str] = Counter()
    for payload in payloads:
        counts.update(tokenize(payload))
    n_keep = max(1, int(len(counts) * keep_ratio)) if len(counts) >= 100 else max(1, len(counts))
    vocab = [PAD_TOKEN]
    vocab.extend(tok for tok, _ in counts.most_common(n_keep) if tok not in {PAD_TOKEN, OOV_TOKEN})
    vocab.append(OOV_TOKEN)
    return vocab


def encode_tokens(tokens: list[str], token_to_id: dict[str, int], none_id: int) -> torch.Tensor:
    pad_id = token_to_id[PAD_TOKEN]
    ids = [token_to_id.get(tok, none_id) for tok in tokens[:MAX_LENGTH]]
    if len(ids) < MAX_LENGTH:
        ids.extend([pad_id] * (MAX_LENGTH - len(ids)))
    return torch.tensor(ids, dtype=torch.long)


def encode_payload(payload: str, token_to_id: dict[str, int], none_id: int) -> torch.Tensor:
    return encode_tokens(tokenize(payload), token_to_id, none_id)


def oov_rate(payload: str, vocab: set[str]) -> tuple[int, int]:
    tokens = tokenize(payload)
    if not tokens:
        return 0, 0
    n_none = sum(1 for tok in tokens if tok not in vocab)
    return n_none, len(tokens)


def save_vocab(path: Path, vocab: list[str]) -> None:
    path.write_text(json.dumps(vocab, ensure_ascii=False, indent=0), encoding="utf-8")


def load_vocab(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))
