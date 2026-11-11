"""Tests for the existing Fake Product Detection API endpoints."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# Check that the root endpoint returns its documented service message.
def test_root_returns_service_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Fake Product Detection API is running"
    }


# Check that the health endpoint reports the service as healthy.
def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Check that a reference product with a matching brand and close price is genuine.
def test_predict_reference_product_with_close_price_is_genuine():
    payload = {"product_name": "AirPods Pro", "brand": "Apple", "price": 24990}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "product_name": "AirPods Pro",
        "brand": "Apple",
        "price": 24990,
        "prediction": "genuine",
    }


# Check that a matching brand with a price more than 30% away is suspicious.
def test_predict_reference_product_with_far_price_is_suspicious():
    payload = {"product_name": "AirPods Pro", "brand": "Apple", "price": 40000}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "suspicious"


# Check that a reference product with a mismatched brand is suspicious.
def test_predict_reference_product_with_wrong_brand_is_suspicious():
    payload = {"product_name": "AirPods Pro", "brand": "Samsung", "price": 24990}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "suspicious"


# Check that an unrecognized product name returns the code's unknown prediction.
def test_predict_unknown_product_returns_unknown():
    payload = {"product_name": "Unknown Product", "brand": "Acme", "price": 100}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "product_name": "Unknown Product",
        "brand": "Acme",
        "price": 100,
        "prediction": "unknown",
    }


# Check that omitting a required request field is rejected with HTTP 422.
def test_predict_missing_required_field_returns_422():
    payload = {"product_name": "AirPods Pro", "brand": "Apple"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422


# Check that a non-numeric price is rejected with HTTP 422.
def test_predict_non_numeric_price_returns_422():
    payload = {"product_name": "AirPods Pro", "brand": "Apple", "price": "not-a-number"}

    response = client.post("/predict", json=payload)

    assert response.status_code == 422
