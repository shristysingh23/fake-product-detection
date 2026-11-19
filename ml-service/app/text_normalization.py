"""Deterministic lexical normalization for OCR text and catalog aliases.

Normalization standardizes text for later matching only. It does not correct
spelling, infer a product, or replace text with a known catalog value.
"""

from __future__ import annotations

import unicodedata


def normalize_text(text: str | None) -> str:
    """Return normalized text, or an empty string for ``None``.

    NFKC compatibility normalization and Unicode case folding run first. Any
    character that is not a Unicode letter or digit becomes a space; this
    standardizes punctuation and special characters as token boundaries while
    preserving letters, digits, model-number components, and unit tokens.
    Repeated whitespace is collapsed and leading/trailing whitespace removed.

    Non-string values other than ``None`` raise ``TypeError`` instead of being
    silently converted to text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        raise TypeError("text must be a string or None.")

    normalized = unicodedata.normalize("NFKC", text).casefold()
    standardized = "".join(
        character if character.isalnum() else " " for character in normalized
    )
    return " ".join(standardized.split())
