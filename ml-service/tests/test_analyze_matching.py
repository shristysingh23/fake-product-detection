"""API integration tests using a fake OCR engine and temporary catalogs."""

import io
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main, ocr
from app.catalog import CatalogLoadError, load_product_catalog
from app.main import app
from app.product_matcher import identify_product as real_identify_product


client = TestClient(app)
EXPECTED_KEYS = {
    "brand", "product", "status", "identification_source", "extracted_text", "ocr_lines"
}


def record(product_id, brand, name):
    return {
        "product_id": product_id,
        "brand": brand,
        "product_name": name,
        "category": "Test category",
        "brand_aliases": [],
        "product_aliases": [],
    }


def load_fixture_catalog(tmp_path, products):
    path = tmp_path / "products.json"
    path.write_text(json.dumps({"schema_version": 1, "products": products}), encoding="utf-8")
    return load_product_catalog(path)


def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (32, 24), "white").save(stream, format="PNG")
    return stream.getvalue()


class FakeEngine:
    def __init__(self, texts, scores=None):
        self.texts = texts
        self.scores = scores or [0.9] * len(texts)

    def predict(self, image):
        box = np.array([[0, 0], [10, 0], [10, 10], [0, 10]])
        return [{"rec_texts": self.texts, "rec_scores": self.scores,
                 "rec_polys": [box for _ in self.texts]}]


@pytest.fixture
def controlled_catalog(monkeypatch):
    previous = getattr(app.state, "product_catalog", None)

    def set_catalog(records):
        app.state.product_catalog = records

    yield set_catalog

    if previous is None:
        if hasattr(app.state, "product_catalog"):
            delattr(app.state, "product_catalog")
    else:
        app.state.product_catalog = previous


def post_image():
    return client.post(
        "/analyze", files={"image": ("test.png", png_bytes(), "image/png")}
    )


def use_engine(monkeypatch, engine):
    monkeypatch.setattr(ocr, "get_ocr_engine", lambda: engine)


def test_identified_response_uses_ocr_lines_and_canonical_catalog_values(
    monkeypatch, tmp_path, controlled_catalog
):
    catalog = load_fixture_catalog(tmp_path, [record("golden-bites", "Sample Foods", "Golden Oat Bites 250g")])
    controlled_catalog(catalog)
    use_engine(monkeypatch, FakeEngine(["Sample Foods", "Golden Oat Bites 250g"], [.95, .88]))
    observed = {}

    def recording_matcher(lines, products):
        observed["lines"] = lines
        return real_identify_product(lines, products)

    monkeypatch.setattr(main, "identify_product", recording_matcher)
    response = post_image()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IDENTIFIED"
    assert body["brand"] == "Sample Foods"
    assert body["product"] == "Golden Oat Bites 250g"
    assert body["identification_source"] == "product_catalog"
    assert body["extracted_text"] == "Sample Foods\nGolden Oat Bites 250g"
    assert body["ocr_lines"] == [
        {"text": "Sample Foods", "confidence": .95},
        {"text": "Golden Oat Bites 250g", "confidence": .88},
    ]
    assert [line.text for line in observed["lines"]] == ["Sample Foods", "Golden Oat Bites 250g"]
    assert [line.confidence for line in observed["lines"]] == [.95, .88]


def test_ambiguous_response_keeps_shared_brand_and_empty_product(
    monkeypatch, tmp_path, controlled_catalog
):
    catalog = load_fixture_catalog(tmp_path, [
        record("cola-zero", "Bright Drinks", "Cola Zero"),
        record("cola-light", "Bright Drinks", "Cola Light"),
    ])
    controlled_catalog(catalog)
    use_engine(monkeypatch, FakeEngine(["Bright Drinks", "Cola Zero", "Cola Light"]))

    body = post_image().json()

    assert body["status"] == "AMBIGUOUS"
    assert body["brand"] == "Bright Drinks"
    assert body["product"] == ""
    assert body["identification_source"] == "product_catalog"


def test_not_found_response_has_non_null_empty_values(monkeypatch, tmp_path, controlled_catalog):
    controlled_catalog(load_fixture_catalog(
        tmp_path, [record("golden-bites", "Sample Foods", "Golden Oat Bites 250g")]
    ))
    use_engine(monkeypatch, FakeEngine(["unrelated", "text"]))

    body = post_image().json()

    assert body["status"] == "NOT_FOUND"
    assert body["brand"] == ""
    assert body["product"] == ""


def test_brand_is_returned_when_product_is_not_identified(
    monkeypatch, tmp_path, controlled_catalog
):
    controlled_catalog(load_fixture_catalog(
        tmp_path, [record("golden-bites", "Sample Foods", "Golden Oat Bites 250g")]
    ))
    use_engine(monkeypatch, FakeEngine(["Sample Foods", "Limited time offer"]))

    body = post_image().json()

    assert body["status"] == "NOT_FOUND"
    assert body["brand"] == "Sample Foods"
    assert body["product"] == ""


def test_empty_ocr_output_and_valid_empty_catalog_return_not_found(
    monkeypatch, tmp_path, controlled_catalog
):
    controlled_catalog(load_fixture_catalog(tmp_path, []))
    use_engine(monkeypatch, FakeEngine([]))

    body = post_image().json()

    assert body["status"] == "NOT_FOUND"
    assert body["brand"] == body["product"] == ""
    assert body["extracted_text"] == ""
    assert body["ocr_lines"] == []


def test_invalid_image_still_returns_existing_validation_error(monkeypatch):
    engine = FakeEngine(["unused"])
    use_engine(monkeypatch, engine)
    response = client.post("/analyze", files={"image": ("bad.png", b"invalid", "image/png")})

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is not a valid image."}


def test_ocr_engine_failure_remains_a_service_error(monkeypatch, controlled_catalog):
    controlled_catalog(())

    class BrokenEngine:
        def predict(self, image):
            raise RuntimeError("private engine details")

    use_engine(monkeypatch, BrokenEngine())
    response = post_image()

    assert response.status_code == 503
    assert response.json() == {"detail": "Text extraction failed. Please try again."}
    assert "private engine details" not in response.text


def test_catalog_loading_failure_is_not_converted_to_not_found(monkeypatch, controlled_catalog):
    controlled_catalog(None)
    use_engine(monkeypatch, FakeEngine([]))

    def fail_catalog_load():
        raise CatalogLoadError("private catalog path")

    monkeypatch.setattr(main, "get_product_catalog", fail_catalog_load)
    response = post_image()

    assert response.status_code == 503
    assert response.json() == {"detail": "Product catalog is unavailable."}
    assert "private catalog path" not in response.text


def test_lifespan_loads_catalog_once_before_serving(monkeypatch):
    previous = getattr(app.state, "product_catalog", None)
    calls = []
    monkeypatch.setattr(main, "get_product_catalog", lambda: calls.append("loaded") or ())
    try:
        with TestClient(app) as lifespan_client:
            assert app.state.product_catalog == ()
            assert lifespan_client.get("/health").json() == {"status": "ok"}
            assert calls == ["loaded"]
        assert calls == ["loaded"]
    finally:
        if previous is None:
            if hasattr(app.state, "product_catalog"):
                delattr(app.state, "product_catalog")
        else:
            app.state.product_catalog = previous


def test_invalid_catalog_prevents_application_startup(monkeypatch):
    previous = getattr(app.state, "product_catalog", None)

    def fail_catalog_load():
        raise CatalogLoadError("private catalog path")

    monkeypatch.setattr(main, "get_product_catalog", fail_catalog_load)
    try:
        with pytest.raises(RuntimeError, match="Product catalog could not be loaded"):
            with TestClient(app):
                pass
    finally:
        if previous is None:
            if hasattr(app.state, "product_catalog"):
                delattr(app.state, "product_catalog")
        else:
            app.state.product_catalog = previous


def test_matcher_failure_is_logged_and_returned_as_service_error(
    monkeypatch, controlled_catalog
):
    controlled_catalog(())
    use_engine(monkeypatch, FakeEngine(["some text"]))

    def fail_matcher(*args, **kwargs):
        raise RuntimeError("private matcher details")

    monkeypatch.setattr(main, "identify_product", fail_matcher)
    response = post_image()

    assert response.status_code == 503
    assert response.json() == {"detail": "Product identification failed. Please try again."}
    assert "private matcher details" not in response.text


def test_response_names_types_and_multipart_field_remain_backend_compatible(
    monkeypatch, controlled_catalog
):
    controlled_catalog(())
    use_engine(monkeypatch, FakeEngine(["unrelated"]))
    response = post_image()
    body = response.json()

    assert response.status_code == 200
    assert set(body) == EXPECTED_KEYS
    assert isinstance(body["brand"], str) and body["brand"] is not None
    assert isinstance(body["product"], str) and body["product"] is not None
    assert isinstance(body["status"], str)
    assert isinstance(body["identification_source"], str)
    assert isinstance(body["extracted_text"], str)
    assert isinstance(body["ocr_lines"], list)
    assert all(set(line) == {"text", "confidence"} for line in body["ocr_lines"])
    wrong_part = client.post("/analyze", files={"file": ("test.png", png_bytes(), "image/png")})
    assert wrong_part.status_code == 422
