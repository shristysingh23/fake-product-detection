"""
OCR for the Fake Product Detection ML service (Day 7).

Pipeline position:   preprocessed image -> OCR -> text lines with confidence

PaddleOCR works in two stages: it first DETECTS where text is in the image,
then RECOGNIZES the characters in each detected region. For each text line we
get the text, a confidence score between 0 and 1, and the four corner points
of its box.

Design notes
- PaddleOCR is heavy, so it is loaded lazily (only on the first OCR call), never
  at import time or server start-up.
- Parsing the engine output is separate from running the engine, so the parsing
  can be tested with a fake engine (no models needed).
- OCR confidence is a model output, not proof that the text is correct. Later
  days compare this text with the genuine product's expected text.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, List, Optional, Protocol

import numpy as np

# PaddleX (used inside PaddleOCR) checks several model servers at start-up, which
# slows start-up and prints noise. We only want models downloaded when needed.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# Lines recognized with a lower confidence than this are dropped by default.
DEFAULT_MIN_CONFIDENCE = 0.5


@dataclass(frozen=True)
class OcrLine:
    """One recognized line of text."""

    text: str
    confidence: float  # 0.0 to 1.0
    box: list  # four [x, y] corner points, or [] if the engine gave no box


@dataclass(frozen=True)
class OcrResult:
    """All recognized lines of one image, in the order the engine returned them."""

    lines: List[OcrLine]

    @property
    def texts(self) -> List[str]:
        return [line.text for line in self.lines]

    @property
    def full_text(self) -> str:
        return "\n".join(self.texts)


class OcrEngine(Protocol):
    """Anything with a predict(image) method, such as PaddleOCR or a test fake."""

    def predict(self, image: np.ndarray) -> Any:
        ...


def _get_field(result: Any, key: str) -> Any:
    """Read a field from top-level, nested ``res``, or ``result.json['res']``."""
    try:
        if key in result:
            return result[key]
    except TypeError:
        pass
    try:
        nested = result["res"]
        if key in nested:
            return nested[key]
    except (KeyError, TypeError):
        pass
    json_view = getattr(result, "json", None)
    if isinstance(json_view, dict):
        nested = json_view.get("res", json_view)
        if key in nested:
            return nested[key]
    return None


def parse_paddle_output(raw_results: Any, min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> OcrResult:
    """Convert PaddleOCR output to lines, skipping blanks and low-confidence text."""
    if raw_results is None:
        return OcrResult(lines=[])
    if isinstance(raw_results, dict):
        raw_results = [raw_results]

    lines: List[OcrLine] = []
    for result in raw_results:
        texts = _get_field(result, "rec_texts")
        if texts is None:
            continue
        scores = _get_field(result, "rec_scores")
        polys = _get_field(result, "rec_polys")
        texts = list(texts)
        scores = list(scores) if scores is not None else []
        polys = list(polys) if polys is not None else []

        for index, raw_text in enumerate(texts):
            text = " ".join(str(raw_text).split())
            if not text:
                continue
            confidence = float(scores[index]) if index < len(scores) else 0.0
            if confidence < min_confidence:
                continue
            box = np.asarray(polys[index]).astype(int).tolist() if index < len(polys) else []
            lines.append(OcrLine(text=text, confidence=confidence, box=box))
    return OcrResult(lines=lines)


_engine: Optional[OcrEngine] = None
_engine_lock = threading.Lock()


def get_ocr_engine() -> OcrEngine:
    """Create the PaddleOCR engine on first use and reuse it afterwards."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                # Imported here on purpose: it is heavy and only needed for real OCR.
                from paddleocr import PaddleOCR

                _engine = PaddleOCR(
                    lang="en",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
    return _engine


def extract_text(
    image: np.ndarray,
    engine: Optional[OcrEngine] = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> OcrResult:
    """Run OCR on one BGR uint8 image (for example PreprocessResult.image)."""
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a numpy array (BGR, uint8).")
    if image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("image must be a non-empty 3-channel (BGR) array.")
    if engine is None:
        engine = get_ocr_engine()
    raw_results = engine.predict(image)
    return parse_paddle_output(raw_results, min_confidence=min_confidence)


def ocr_result_to_dict(result: OcrResult) -> dict:
    """Plain-dict form of an OcrResult, safe to save as JSON."""
    return {
        "lines": [
            {"text": line.text, "confidence": line.confidence, "box": line.box}
            for line in result.lines
        ],
        "full_text": result.full_text,
    }
