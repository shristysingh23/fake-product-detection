from io import BytesIO
import logging
import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.analysis import run_ocr_on_bytes
from app.schemas import AnalyzeResponse, OcrLineOut

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional: load the OCR models at start-up so the first request is not slow.
    # Off by default so tests and quick runs start fast. Enable with OCR_PRELOAD=1.
    if os.environ.get("OCR_PRELOAD") == "1":
        from app.ocr import get_ocr_engine

        get_ocr_engine()
    yield

app = FastAPI(title="Fake Product Detection API", lifespan=lifespan)


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
async def analyze(image: UploadFile = File(...)):
    """Day 4 dummy implementation per the 20-day plan; real analysis replaces it on Days 6-13."""
    # Check the declared content type before reading or inspecting the uploaded bytes.
    accepted_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in accepted_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a JPEG, PNG or WebP image.",
        )

    # Read the upload into memory only; the image is never saved to disk.
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Verify that the declared image file contains readable image data.
    try:
        with Image.open(BytesIO(image_bytes)) as uploaded_image:
            uploaded_image.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image.",
        )

    try:
        ocr_result = await run_in_threadpool(run_ocr_on_bytes, image_bytes)
    except ValueError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as error:
        # Log only the exception class and traceback frames, never the message or upload data.
        logger.error(
            "OCR failed (%s)\n%s",
            type(error).__name__,
            "".join(traceback.format_tb(error.__traceback__)),
        )
        raise HTTPException(status_code=503, detail="Text extraction failed. Please try again.")

    return AnalyzeResponse(
        brand="MAGGI",
        product="2-Minute Noodles",
        status="ANALYSIS_PENDING",
        identification_source="placeholder",
        extracted_text=ocr_result.full_text,
        ocr_lines=[
            OcrLineOut(text=line.text, confidence=line.confidence)
            for line in ocr_result.lines
        ],
    )
