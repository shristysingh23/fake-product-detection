"""Tests for app/analysis.py (bytes -> preprocessing -> OCR). Fake engine, no Paddle."""

import io

import pytest
from PIL import Image

from app.analysis import OCR_MAX_SIDE, run_ocr_on_bytes


class RecordingEngine:
    """Remembers the image it was given so tests can inspect it."""

    def __init__(self, raw=None):
        self.raw = raw if raw is not None else []
        self.received = None

    def predict(self, image):
        self.received = image
        return self.raw


def png_bytes(size):
    buffer = io.BytesIO()
    Image.new("RGB", size, (255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_run_ocr_returns_engine_text():
    engine = RecordingEngine([{"rec_texts": ["Maggi"], "rec_scores": [0.9]}])
    result = run_ocr_on_bytes(png_bytes((200, 100)), engine=engine)
    assert result.texts == ["Maggi"]


def test_run_ocr_downsizes_large_images():
    engine = RecordingEngine()
    run_ocr_on_bytes(png_bytes((3000, 2000)), engine=engine)
    assert max(engine.received.shape[:2]) <= OCR_MAX_SIDE


def test_run_ocr_without_preprocessing_keeps_size():
    engine = RecordingEngine()
    run_ocr_on_bytes(png_bytes((300, 200)), engine=engine, preprocess=False)
    assert engine.received.shape[:2] == (200, 300)


def test_run_ocr_rejects_non_image_bytes():
    engine = RecordingEngine()
    with pytest.raises(ValueError):
        run_ocr_on_bytes(b"not an image", engine=engine)
    assert engine.received is None
