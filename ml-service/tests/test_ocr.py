"""Day 7 tests for app/ocr.py.

Most tests use a fake engine, so they need no PaddleOCR and no model downloads.
One opt-in integration test runs the real engine (set RUN_OCR_INTEGRATION=1).
"""

import json
import os

import numpy as np
import pytest

from app import ocr
from app.ocr import OcrResult, extract_text, ocr_result_to_dict, parse_paddle_output

BOX_A = [[10, 10], [110, 10], [110, 40], [10, 40]]
BOX_B = [[10, 60], [210, 60], [210, 90], [10, 90]]


def make_raw(texts, scores, boxes):
    """Build fake raw output in the same shape PaddleOCR returns (top-level fields)."""
    return [{"rec_texts": texts, "rec_scores": scores, "rec_polys": [np.array(box) for box in boxes]}]


class FakeEngine:
    """Stands in for PaddleOCR: remembers the image it got and returns canned output."""

    def __init__(self, raw):
        self.raw = raw
        self.received = None

    def predict(self, image):
        self.received = image
        return self.raw


def blank_image():
    return np.full((100, 300, 3), 255, dtype=np.uint8)


def test_parse_extracts_text_confidence_and_box():
    result = parse_paddle_output(make_raw(["MAGGI", "2-MINUTE NOODLES"], [0.99, 0.95], [BOX_A, BOX_B]))
    assert result.texts == ["MAGGI", "2-MINUTE NOODLES"]
    assert result.lines[0].confidence == pytest.approx(0.99)
    assert result.lines[0].box == BOX_A
    assert result.lines[1].box == BOX_B


def test_parse_handles_nested_res_layout():
    raw = [{"res": {"rec_texts": ["MAGGI"], "rec_scores": [0.9], "rec_polys": [np.array(BOX_A)]}}]
    result = parse_paddle_output(raw)
    assert result.texts == ["MAGGI"]
    assert result.lines[0].box == BOX_A


def test_parse_accepts_single_dict():
    result = parse_paddle_output({"rec_texts": ["NET WT 70g"], "rec_scores": [0.9]})
    assert result.texts == ["NET WT 70g"]


def test_parse_skips_blank_lines():
    raw = make_raw(["MAGGI", "   ", ""], [0.9, 0.9, 0.9], [BOX_A, BOX_B, BOX_B])
    assert parse_paddle_output(raw).texts == ["MAGGI"]


def test_parse_collapses_whitespace():
    raw = make_raw(["NET   WT  70g"], [0.9], [BOX_A])
    assert parse_paddle_output(raw).texts == ["NET WT 70g"]


def test_parse_filters_by_min_confidence():
    raw = make_raw(["MAGGI", "MAGG1"], [0.95, 0.30], [BOX_A, BOX_B])
    assert parse_paddle_output(raw).texts == ["MAGGI"]
    assert parse_paddle_output(raw, min_confidence=0.0).texts == ["MAGGI", "MAGG1"]


def test_parse_handles_missing_scores_and_boxes():
    raw = [{"rec_texts": ["MAGGI"]}]
    kept = parse_paddle_output(raw, min_confidence=0.0)
    assert kept.lines[0].confidence == 0.0
    assert kept.lines[0].box == []
    assert parse_paddle_output(raw).lines == []


def test_parse_handles_empty_output():
    for raw in ([], None, [{"rec_texts": []}]):
        result = parse_paddle_output(raw)
        assert result.lines == []
        assert result.full_text == ""


def test_full_text_joins_lines_with_newlines():
    raw = make_raw(["MAGGI", "2-MINUTE NOODLES"], [0.9, 0.9], [BOX_A, BOX_B])
    assert parse_paddle_output(raw).full_text == "MAGGI\n2-MINUTE NOODLES"


def test_extract_text_passes_image_to_engine():
    image = blank_image()
    engine = FakeEngine(make_raw(["MAGGI"], [0.9], [BOX_A]))
    result = extract_text(image, engine=engine)
    assert engine.received is image
    assert isinstance(result, OcrResult)
    assert result.texts == ["MAGGI"]


def test_extract_text_does_not_create_real_engine_when_given_one(monkeypatch):
    def boom():
        raise AssertionError("real engine must not be created")

    monkeypatch.setattr(ocr, "get_ocr_engine", boom)
    extract_text(blank_image(), engine=FakeEngine([]))


def test_extract_text_uses_default_engine_when_none_given(monkeypatch):
    monkeypatch.setattr(ocr, "get_ocr_engine", lambda: FakeEngine(make_raw(["LAYS"], [0.9], [BOX_A])))
    assert extract_text(blank_image()).texts == ["LAYS"]


def test_extract_text_rejects_bad_input():
    with pytest.raises(TypeError):
        extract_text(b"not an array", engine=FakeEngine([]))
    with pytest.raises(ValueError):
        extract_text(np.zeros((0, 0, 3), dtype=np.uint8), engine=FakeEngine([]))
    with pytest.raises(ValueError):
        extract_text(np.zeros((50, 50), dtype=np.uint8), engine=FakeEngine([]))


def test_result_to_dict_is_json_serializable():
    data = ocr_result_to_dict(parse_paddle_output(make_raw(["MAGGI"], [0.9], [BOX_A])))
    assert set(data.keys()) == {"lines", "full_text"}
    assert data["lines"][0]["text"] == "MAGGI"
    assert json.loads(json.dumps(data)) == data


@pytest.mark.ocr_integration
@pytest.mark.skipif(
    os.environ.get("RUN_OCR_INTEGRATION") != "1",
    reason="Set RUN_OCR_INTEGRATION=1 to run the real PaddleOCR test (downloads models on first run).",
)
def test_real_paddleocr_reads_simple_text():
    import cv2

    image = np.full((200, 700, 3), 255, dtype=np.uint8)
    cv2.putText(image, "MAGGI NOODLES", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 0), 5, cv2.LINE_AA)
    result = extract_text(image, min_confidence=0.0)
    assert "MAGGI" in result.full_text.upper()
