"""Tests for /analyze with OCR output. A fake engine is used, so no Paddle is needed."""

import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app import ocr
from app import analysis
from app.main import app

client = TestClient(app)

NEW_KEYS = {"brand", "product", "status", "identification_source", "extracted_text", "ocr_lines"}


class FakeEngine:
    """Returns canned PaddleOCR-style output and counts how often it is called."""

    def __init__(self, raw):
        self.raw = raw
        self.calls = 0
        self.received = None

    def predict(self, image):
        self.calls += 1
        self.received = image.copy()
        return self.raw


class BoomEngine:
    """An engine that always fails, to test the 503 path."""

    def predict(self, image):
        raise RuntimeError("engine exploded")


def raw(texts, scores):
    box = np.array([[0, 0], [10, 0], [10, 10], [0, 10]])
    return [{"rec_texts": texts, "rec_scores": scores, "rec_polys": [box for _ in texts]}]


def png_bytes(size=(120, 80)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def post_png(data=None):
    return client.post("/analyze", files={"image": ("p.png", data or png_bytes(), "image/png")})


def use_engine(monkeypatch, engine):
    monkeypatch.setattr(ocr, "get_ocr_engine", lambda: engine)


def test_analyze_returns_extracted_text_and_lines(monkeypatch):
    use_engine(monkeypatch, FakeEngine(raw(["Maggi", "2-Minute"], [1.0, 0.8])))
    response = post_png()
    assert response.status_code == 200
    body = response.json()
    assert body["extracted_text"] == "Maggi\n2-Minute"
    assert body["ocr_lines"] == [
        {"text": "Maggi", "confidence": 1.0},
        {"text": "2-Minute", "confidence": 0.8},
    ]


def test_analyze_reports_not_found_without_matching_catalog_product(monkeypatch):
    use_engine(monkeypatch, FakeEngine(raw(["Maggi"], [0.9])))
    body = post_png().json()
    assert body["brand"] == "MAGGI"
    assert body["product"] == ""
    assert body["status"] == "NOT_FOUND"
    assert body["identification_source"] == "product_catalog"


def test_analyze_response_has_exact_keys(monkeypatch):
    use_engine(monkeypatch, FakeEngine(raw(["Maggi"], [0.9])))
    assert set(post_png().json().keys()) == NEW_KEYS


def test_analyze_with_no_text_returns_empty_fields(monkeypatch):
    use_engine(monkeypatch, FakeEngine([]))
    response = post_png()
    assert response.status_code == 200
    assert response.json()["extracted_text"] == ""
    assert response.json()["ocr_lines"] == []


def test_analyze_drops_low_confidence_lines(monkeypatch):
    use_engine(monkeypatch, FakeEngine(raw(["Maggi", "noise"], [0.9, 0.3])))
    assert post_png().json()["extracted_text"] == "Maggi"


def test_analyze_calls_engine_once(monkeypatch):
    engine = FakeEngine(raw(["Maggi"], [0.9]))
    use_engine(monkeypatch, engine)
    post_png()
    assert engine.calls == 1


def test_analyze_preprocesses_large_upload_before_ocr(monkeypatch):
    engine = FakeEngine(raw(["Maggi"], [0.95]))
    use_engine(monkeypatch, engine)

    real_preprocess_image = analysis.preprocess_image
    preprocessing_calls = []
    preprocessed_images = []

    def recording_preprocess_image(data, max_side=1024):
        preprocessing_calls.append((data, max_side))
        result = real_preprocess_image(data, max_side=max_side)
        preprocessed_images.append(result.image.copy())
        return result

    monkeypatch.setattr(analysis, "preprocess_image", recording_preprocess_image)

    # 2400 x 1800 exceeds OCR_MAX_SIDE, so the HTTP path must resize it.
    response = client.post(
        "/analyze",
        files={"image": ("large.png", png_bytes(size=(2400, 1800)), "image/png")},
    )

    assert response.status_code == 200
    assert len(preprocessing_calls) == 1
    assert preprocessing_calls[0][1] == analysis.OCR_MAX_SIDE
    assert engine.calls == 1
    assert engine.received is not None
    assert max(engine.received.shape[:2]) <= analysis.OCR_MAX_SIDE
    assert np.array_equal(engine.received, preprocessed_images[0])
    body = response.json()
    assert body["extracted_text"] == "Maggi"
    assert body["ocr_lines"] == [{"text": "Maggi", "confidence": 0.95}]


def test_analyze_returns_503_when_ocr_fails(monkeypatch):
    use_engine(monkeypatch, BoomEngine())
    response = post_png()
    assert response.status_code == 503
    assert response.json() == {"detail": "Text extraction failed. Please try again."}
    assert "exploded" not in response.text


def test_analyze_rejects_bad_file_without_running_ocr(monkeypatch):
    engine = FakeEngine(raw(["Maggi"], [0.9]))
    use_engine(monkeypatch, engine)
    response = client.post("/analyze", files={"image": ("a.txt", b"hello", "text/plain")})
    assert response.status_code == 400
    assert engine.calls == 0


def test_analyze_missing_image_is_422_without_running_ocr(monkeypatch):
    engine = FakeEngine(raw(["Maggi"], [0.9]))
    use_engine(monkeypatch, engine)
    response = client.post("/analyze", files={"file": ("p.png", png_bytes(), "image/png")})
    assert response.status_code == 422
    assert engine.calls == 0
