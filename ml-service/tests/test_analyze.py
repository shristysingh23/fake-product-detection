"""Tests for POST /analyze and its Day 4 dummy response contract."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# Check that a valid request returns the complete fixed dummy response.
def test_analyze_valid_request_returns_dummy_response():
    payload = {"product_name": "AirPods Pro", "brand": "Apple", "price": 24999}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "product_name",
        "brand",
        "price",
        "verdict",
        "confidence",
        "reasons",
        "analysis_mode",
    }
    assert body["product_name"] == payload["product_name"]
    assert body["brand"] == payload["brand"]
    assert body["price"] == payload["price"]
    assert body["verdict"] == "SUSPICIOUS"
    assert body["confidence"] == 0.5
    assert isinstance(body["reasons"], list)
    assert all(isinstance(reason, str) for reason in body["reasons"])
    assert body["reasons"] == [
        "Dummy response: real analysis is not implemented yet"
    ]
    assert body["analysis_mode"] == "dummy"


# Check that surrounding whitespace is removed from product_name.
def test_analyze_trims_product_name():
    payload = {"product_name": "  AirPods Pro  ", "brand": "Apple", "price": 24999}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json()["product_name"] == "AirPods Pro"


# Check that a missing product_name is rejected.
def test_analyze_missing_product_name_returns_422():
    response = client.post("/analyze", json={"brand": "Apple", "price": 10})

    assert response.status_code == 422


# Check that a missing brand is rejected.
def test_analyze_missing_brand_returns_422():
    response = client.post("/analyze", json={"product_name": "Item", "price": 10})

    assert response.status_code == 422


# Check that a missing price is rejected.
def test_analyze_missing_price_returns_422():
    response = client.post("/analyze", json={"product_name": "Item", "brand": "A"})

    assert response.status_code == 422


# Check that an empty product_name is rejected.
def test_analyze_empty_product_name_returns_422():
    payload = {"product_name": "", "brand": "Apple", "price": 10}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


# Check that a whitespace-only brand is stripped and rejected.
def test_analyze_whitespace_brand_returns_422():
    payload = {"product_name": "Item", "brand": "   ", "price": 10}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


# Check that zero is rejected as a price.
def test_analyze_zero_price_returns_422():
    payload = {"product_name": "Item", "brand": "A", "price": 0}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


# Check that a negative price is rejected.
def test_analyze_negative_price_returns_422():
    payload = {"product_name": "Item", "brand": "A", "price": -1}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


# Check that a non-numeric price is rejected.
def test_analyze_non_numeric_price_returns_422():
    payload = {"product_name": "Item", "brand": "A", "price": "abc"}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 422


# Check that an empty JSON object is missing required fields.
def test_analyze_empty_json_returns_422():
    response = client.post("/analyze", json={})

    assert response.status_code == 422


# Check that a plain-text body is rejected as invalid input.
def test_analyze_plain_text_body_returns_422():
    response = client.post(
        "/analyze",
        content="not JSON",
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 422


# Check that unknown product names still receive the same dummy response.
def test_analyze_unknown_product_returns_dummy_response():
    payload = {"product_name": "Not in demo catalog", "brand": "Acme", "price": 42}

    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "product_name": "Not in demo catalog",
        "brand": "Acme",
        "price": 42,
        "verdict": "SUSPICIOUS",
        "confidence": 0.5,
        "reasons": ["Dummy response: real analysis is not implemented yet"],
        "analysis_mode": "dummy",
    }


# Check that GET is not allowed on the POST-only analysis path.
def test_analyze_get_method_returns_405():
    response = client.get("/analyze")

    assert response.status_code == 405


# Check that OpenAPI documents POST /analyze.
def test_openapi_lists_analyze_post_path():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "post" in response.json()["paths"]["/analyze"]


# Check that the existing predict endpoint keeps its previous response contract.
def test_predict_regression_reference_product_is_unchanged():
    payload = {"product_name": "AirPods Pro", "brand": "Apple", "price": 24990}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "product_name": "AirPods Pro",
        "brand": "Apple",
        "price": 24990,
        "prediction": "genuine",
    }
