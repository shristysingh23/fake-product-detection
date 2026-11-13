"""Tests for the image upload dummy contract on POST /analyze."""

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)
EXPECTED_BODY = {
    "brand": "MAGGI",
    "product": "2-Minute Noodles",
    "status": "ANALYSIS_PENDING",
}


def make_image(image_format):
    """Create a tiny valid image in memory for multipart requests."""
    stream = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(stream, format=image_format)
    return stream.getvalue()


# Check that a valid PNG upload returns the exact dummy response.
def test_analyze_valid_png_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.png", make_image("PNG"), "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == EXPECTED_BODY


# Check that a valid JPEG upload returns the same dummy response.
def test_analyze_valid_jpeg_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.jpg", make_image("JPEG"), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == EXPECTED_BODY


# Check that a valid WebP upload returns the same dummy response.
def test_analyze_valid_webp_returns_dummy_response():
    response = client.post(
        "/analyze",
        files={"image": ("product.webp", make_image("WEBP"), "image/webp")},
    )

    assert response.status_code == 200
    assert response.json() == EXPECTED_BODY


# Check that the response contains only the three contract fields.
def test_analyze_response_has_exact_keys():
    response = client.post(
        "/analyze",
        files={"image": ("product.png", make_image("PNG"), "image/png")},
    )

    assert set(response.json()) == {"brand", "product", "status"}


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
