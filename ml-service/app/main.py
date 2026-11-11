from fastapi import FastAPI
from app.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Fake Product Detection API")


@app.get("/")
def root():
    return {"message": "Fake Product Detection API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}

from pydantic import BaseModel


class ProductRequest(BaseModel):
    product_name: str
    brand: str
    price: float


@app.post("/predict")
def predict(product: ProductRequest):

    # Demo reference data
    known_products = {
        "AirPods Pro": {
            "brand": "Apple",
            "price": 24990
        },
        "iPhone 15": {
            "brand": "Apple",
            "price": 69900
        }
    }

    product_info = known_products.get(product.product_name)

    if product_info is None:
        prediction = "unknown"

    elif product.brand.lower() != product_info["brand"].lower():
        prediction = "suspicious"

    elif abs(product.price - product_info["price"]) > product_info["price"] * 0.30:
        prediction = "suspicious"

    else:
        prediction = "genuine"

    return {
        "product_name": product.product_name,
        "brand": product.brand,
        "price": product.price,
        "prediction": prediction
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(product: AnalyzeRequest):
    """Return a Day 4 dummy result; Days 6-10 will replace this logic."""
    return {
        "product_name": product.product_name,
        "brand": product.brand,
        "price": product.price,
        "verdict": "SUSPICIOUS",
        "confidence": 0.5,
        "reasons": ["Dummy response: real analysis is not implemented yet"],
        "analysis_mode": "dummy",
    }
