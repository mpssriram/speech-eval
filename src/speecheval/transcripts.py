"""Transcript normalization and ASR comparison."""

from __future__ import annotations

import re

from num2words import num2words


def _number_to_words(match: re.Match[str]) -> str:
    return str(num2words(int(match.group(0)))).replace("-", " ")


def normalize_tokens(text: str) -> list[str]:
    """Normalize transcript text into lowercase comparison tokens."""
    text = text.lower().replace("&", " and ")
    text = re.sub(r"\d+", _number_to_words, text)
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"['-]", "", text)
    text = re.sub(r"[^a-z]+", " ", text)
    return text.split()
