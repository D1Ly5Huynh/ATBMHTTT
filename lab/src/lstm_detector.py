"""LSTM XSS detector — architecture aligned with Pasini artifact (sigmoid, embed 8)."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class LSTMDetector(nn.Module):
    def __init__(self, vocab_size: int, embedding_dim: int = 8, hidden: int = 128) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden, batch_first=True)
        self.hidden2tag = nn.Linear(hidden, 1)

    def forward(self, token_ids: torch.Tensor, pad_id: int | None = None) -> torch.Tensor:
        embedded = self.embedding(token_ids)
        output, _ = self.lstm(embedded)
        if pad_id is None:
            pooled = output[:, -1, :]
        else:
            mask = (token_ids != pad_id).unsqueeze(-1).to(output.dtype)
            pooled = (output * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        return torch.sigmoid(self.hidden2tag(pooled))
