"""
Glue between the API and the OCR pipeline.

uploaded image bytes -> preprocessing (OpenCV) -> OCR (PaddleOCR) -> OcrResult

Kept separate from main.py so it can be tested without starting the API.
"""

from __future__ import annotations

import threading
from typing import Optional

from app.ocr import DEFAULT_MIN_CONFIDENCE, OcrEngine, OcrResult, extract_text
from app.preprocessing import decode_image, preprocess_image

# Phone photos are often 4000 px wide. Shrinking to 1600 px keeps small print
# readable while making OCR much faster. Revisit when we have a labelled test set.
OCR_MAX_SIDE = 1600

# PaddleOCR is not guaranteed to be thread-safe, and FastAPI runs normal (sync)
# endpoints in a thread pool, so only one OCR call may run at a time.
_ocr_lock = threading.Lock()


def run_ocr_on_bytes(
    data: bytes,
    engine: Optional[OcrEngine] = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    preprocess: bool = True,
    max_side: int = OCR_MAX_SIDE,
) -> OcrResult:
    """Decode uploaded image bytes, optionally preprocess them, and run OCR.

    Raises ValueError if the bytes cannot be decoded as an image.
    """
    if preprocess:
        image = preprocess_image(data, max_side=max_side).image
    else:
        image = decode_image(data)
    with _ocr_lock:
        return extract_text(image, engine=engine, min_confidence=min_confidence)
