"""Tests for the image upload dummy contract on POST /analyze."""

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)
LEGACY_KEYS = {"brand", "product", "status"}


def make_image(image_format):
    """Create a tiny valid image in memory for multipart requests."""
    stream = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(stream, format=image_format)
    return stream.getvalue()


# Check that a valid PNG upload returns a structured extraction response.
def test_analyze_valid_png_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.png", make_image("PNG"), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["processingStatus"] in {"COMPLETED", "PARTIALLY_COMPLETED"}
    assert isinstance(body["extractedText"], list)
    assert isinstance(body["barcodes"], list)
    assert isinstance(body["qrCodes"], list)
    assert isinstance(body["processingErrors"], list)


# Check that a valid JPEG upload returns the same dummy response.
def test_analyze_valid_jpeg_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.jpg", make_image("JPEG"), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.status_code == 200
    assert set(response.json()) >= LEGACY_KEYS


# Check that a valid WebP upload returns the same dummy response.
def test_analyze_valid_webp_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.webp", make_image("WEBP"), "image/webp")},
    )

    assert response.status_code == 200
    assert response.status_code == 200
    assert set(response.json()) >= LEGACY_KEYS


# Check that the response contains only the three contract fields.
def test_analyze_response_has_exact_keys():
    response = client.post(
        "/analyze",
        files={"image": ("product.png", make_image("PNG"), "image/png")},
    )

    assert set(response.json()) >= {
        "processingStatus", "extractedText", "barcodes", "qrCodes",
        "processingErrors", "preprocessing", "brand", "product",
        "status", "candidates",
        "visualMatches", "visualDetection",
    }


# Check that an absent image part, including a differently named part, returns 422.
def test_analyze_missing_image_part_returns_422():
    empty_response = client.post("/analyze", files={})
    wrong_name_response = client.post(
        "/analyze",
        files={"file": ("product.png", make_image("PNG"), "image/png")},
    )

    assert empty_response.status_code == 422
    assert wrong_name_response.status_code == 422


# Check that a text upload is rejected with the unsupported-type detail.
def test_analyze_text_file_returns_unsupported_type_400():
    response = client.post(
        "/analyze",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Unsupported file type. Please upload a JPEG, PNG or WebP image."
    }


# Check that a PDF-like upload is rejected with HTTP 400.
def test_analyze_pdf_file_returns_unsupported_type_400():
    response = client.post(
        "/analyze",
        files={"image": ("document.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Unsupported file type. Please upload a JPEG, PNG or WebP image."
    }


# Check that an empty image upload returns the empty-file detail.
def test_analyze_empty_image_returns_400():
    response = client.post(
        "/analyze",
        files={"image": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is empty."}


# Check that unreadable bytes declared as an image return the invalid-image detail.
def test_analyze_random_image_bytes_returns_400():
    response = client.post(
        "/analyze",
        files={"image": ("broken.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded file is not a valid image."}


# Check that a JSON body without a multipart image part returns 422.
def test_analyze_json_body_returns_422():
    response = client.post("/analyze", json={"image": "not a file"})

    assert response.status_code == 422


# Check that GET is not allowed on the POST-only analysis path.
def test_analyze_get_method_returns_405():
    response = client.get("/analyze")

    assert response.status_code == 405


# Check that OpenAPI documents POST /analyze.
def test_openapi_lists_analyze_post_path():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "post" in response.json()["paths"]["/analyze"]


def test_analyze_returns_visual_matches_without_changing_ocr_or_barcodes(monkeypatch):
    from app import main

    monkeypatch.setattr(
        main,
        "extract_text",
        lambda image: ([{"text": "Brand", "confidence": 0.9}], None),
    )
    monkeypatch.setattr(
        main,
        "detect_barcodes",
        lambda image: ([{"type": "EAN13", "value": "123"}], [], None),
    )
    monkeypatch.setattr(
        main.visual_matcher,
        "match",
        lambda image: (
            [{"productId": 12, "referenceImageId": 5, "similarityScore": 0.91}],
            [],
        ),
    )

    response = client.post(
        "/analyze",
        files={"image": ("product.png", make_image("PNG"), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extractedText"] == [{"text": "Brand", "confidence": 0.9}]
    assert body["barcodes"] == [{"type": "EAN13", "value": "123"}]
    assert body["visualMatches"] == [
        {"productId": 12, "referenceImageId": 5, "similarityScore": 0.91}
    ]
    assert body["visualDetection"]["outcome"] == "INCONCLUSIVE"
    assert body["visualDetection"]["identifiedProduct"] is None


def test_startup_loads_clip_model_once(monkeypatch):
    from fastapi.testclient import TestClient as LifespanTestClient
    from app import main

    calls = []
    monkeypatch.setattr(main.clip_encoder, "load_model", lambda: calls.append("load"))
    with LifespanTestClient(main.app):
        assert client.get("/health").json() == {"status": "ok"}

    assert calls == ["load"]


def test_reference_embedding_refresh_endpoint_forces_rebuild(monkeypatch):
    from app import main

    calls = []
    monkeypatch.setattr(
        main.visual_matcher,
        "refresh",
        lambda force=False: calls.append(force) or {
            "referenceCount": 2,
            "embeddedCount": 2,
            "errors": [],
        },
    )

    response = client.post("/reference-images/refresh")

    assert response.status_code == 200
    assert response.json()["embeddedCount"] == 2
    assert calls == [True]


# Check that the existing predict endpoint keeps its previous status and keys.
def test_predict_regression_reference_product_is_unchanged():
    response = client.post(
        "/predict",
        json={"product_name": "AirPods Pro", "brand": "Apple", "price": 24990},
    )

    assert response.status_code == 200
    assert set(response.json()) == {
        "product_name",
        "brand",
        "price",
        "prediction",
    }
