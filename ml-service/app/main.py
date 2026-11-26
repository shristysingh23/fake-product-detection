from io import BytesIO
import asyncio
from contextlib import asynccontextmanager
import logging

import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.detection import detect_barcodes
from app.schemas import AnalyzeResponse
from app.preprocessing import preprocess_image
from app.ocr import extract_text
from app.clip_service import ClipImageEncoder, ClipModelLoadError
from app.visual_matching import (
    BackendReferenceClient,
    ReferenceServiceError,
    VisualMatcher,
)
from app.visual_analysis import VisualDetectionEngine

logger = logging.getLogger(__name__)
clip_encoder = ClipImageEncoder()
visual_matcher = VisualMatcher(clip_encoder, BackendReferenceClient())
visual_detection_engine = VisualDetectionEngine()


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        await asyncio.to_thread(clip_encoder.load_model)
    except ClipModelLoadError:
        logger.exception("CLIP is unavailable; OCR and barcode extraction remain enabled.")
    yield


app = FastAPI(title="Fake Product Detection API", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Fake Product Detection API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reference-images/refresh")
def refresh_reference_embeddings():
    """Force regeneration of cached CLIP embeddings from Spring reference images."""
    try:
        return visual_matcher.refresh(force=True)
    except ReferenceServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

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
    """Extract OCR text and identifier values from a product image."""
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
        preprocessed, preprocessing = preprocess_image(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    processing_errors = []

    try:
        extracted_text, ocr_error = extract_text(preprocessed)
        if ocr_error:
            processing_errors.append(ocr_error)
    except Exception as exc:
        extracted_text = []
        processing_errors.append("OCR processing failed.")

    try:
        barcodes, qr_codes, detection_error = detect_barcodes(preprocessed)
        if detection_error:
            processing_errors.append(detection_error)
    except Exception:
        barcodes = []
        qr_codes = []
        processing_errors.append("Barcode or QR processing failed.")

    try:
        rgb_image = cv2.cvtColor(preprocessed, cv2.COLOR_BGR2RGB)
        visual_matches, visual_errors = visual_matcher.match(
            Image.fromarray(rgb_image)
        )
        processing_errors.extend(visual_errors)
    except Exception:
        visual_matches = []
        visual_errors = ["CLIP visual matching failed."]
        processing_errors.append("CLIP visual matching failed.")

    try:
        visual_detection = visual_detection_engine.analyze(
            preprocessed,
            visual_matcher.cached_references(),
            visual_matches,
            extracted_text,
            barcodes,
            qr_codes,
            preprocessing,
            visual_errors,
        )
    except Exception:
        logger.exception("Visual counterfeit analysis could not be completed.")
        processing_errors.append("Visual counterfeit analysis could not be completed.")
        visual_detection = visual_detection_engine.unavailable(
            "Visual evidence comparison failed; no detection outcome is supported."
        )

    if extracted_text:
        brand = extracted_text[0]["text"]
        product = " ".join(region["text"] for region in extracted_text[1:3])
    else:
        brand = None
        product = None

    status = "NOT_IDENTIFIED"
    processing_status = "COMPLETED" if not processing_errors else "PARTIALLY_COMPLETED"

    return {
        "processingStatus": processing_status,
        "extractedText": extracted_text,
        "barcodes": barcodes,
        "qrCodes": qr_codes,
        "processingErrors": processing_errors,
        "preprocessing": preprocessing,
        "brand": brand,
        "product": product,
        "status": status,
        "candidates": [],
        "visualMatches": visual_matches,
        "visualDetection": visual_detection,
    }
