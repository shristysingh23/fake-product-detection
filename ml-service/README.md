# ML Service (FastAPI)

A FastAPI service for the Fake Product Detection project.

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The first ML-service startup downloads the pretrained `openai/clip-vit-base-patch32`
model and processor from Hugging Face into the local Transformers cache. PyTorch
uses CPU by default and automatically selects CUDA when available. Set
`REFERENCE_BACKEND_URL` if Spring Boot is not reachable at
`http://127.0.0.1:8080`.

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://127.0.0.1:8000/docs

## Test

```powershell
pytest -v
```

## Endpoints

- `GET /` returns `message`.
- `GET /health` returns `status`.
- `POST /predict` accepts `product_name`, `brand`, and `price`. It retains its legacy demo behavior.
- `POST /analyze` accepts one `image` file as `multipart/form-data`.

### POST /analyze

Supported formats: JPEG, PNG, and WebP. Maximum input size: 10 MB. The response includes `visualMatches`, ranked by CLIP cosine similarity against
genuine reference images served by Spring Boot, and `visualDetection`, a separate
preliminary evidence report:

```json
{
  "processingStatus": "COMPLETED",
  "extractedText": [
    {"text": "MAGGI", "confidence": 0.98},
    {"text": "2-Minute Noodles", "confidence": 0.95}
  ],
  "barcodes": [
    {"type": "EAN13", "value": "8901234567890"}
  ],
  "qrCodes": [],
  "processingErrors": [],
  "preprocessing": {
    "originalDimensions": {"width": 1200, "height": 800},
    "format": "JPEG",
    "orientationCorrected": true,
    "blurScore": 350.4,
    "preprocessed": true
  },
  "brand": "MAGGI",
  "product": "2-Minute Noodles",
  "status": "NOT_IDENTIFIED",
  "candidates": [],
  "visualMatches": [
    {"productId": 12, "referenceImageId": 5, "similarityScore": 0.91}
  ],
  "visualDetection": {
    "outcome": "INCONCLUSIVE",
    "overallConfidence": null,
    "calibrationStatus": "NOT_CALIBRATED",
    "identifiedProduct": {
      "productId": 12,
      "brand": "MAGGI",
      "productName": "2-Minute Noodles",
      "identificationConfidence": 0.9,
      "identificationEvidence": "OCR_BRAND_AND_PRODUCT"
    },
    "clipSimilarityScore": 0.91,
    "logoComparison": {"status": "NOT_AVAILABLE"},
    "packagingComparison": {
      "status": "COMPARABLE",
      "structuralSimilarity": 0.91,
      "colorSimilarity": 0.84,
      "bestReferenceImageId": 5,
      "referencesCompared": []
    },
    "ocrDiscrepancies": {
      "status": "NO_SIGNIFICANT_DIFFERENCE",
      "mismatchRatio": 0.0,
      "missingExpectedTokens": [],
      "unexpectedObservedTokens": [],
      "confidentRegions": 3
    },
    "barcodeEvidence": {
      "status": "MATCH",
      "observedValues": ["8901234567890"],
      "expectedValue": "8901234567890",
      "note": "A barcode match is not proof of authenticity."
    },
    "imageQuality": {
      "status": "ACCEPTABLE",
      "width": 1200,
      "height": 800,
      "blurScore": 350.4,
      "issues": []
    },
    "suspiciousObservations": [],
    "referenceIssues": [],
    "explanation": "Thresholds require validation before classification."
  }
}
```

OCR engines are loaded lazily and reused. PaddleOCR or EasyOCR is used when installed; without an OCR engine, processing succeeds only as far as barcode/detection and reports `OCR engine unavailable`. Barcode support uses OpenCV and optional pyzbar decoding. OCR or barcode failures are isolated and do not prevent the other stage from running.

CLIP's image encoder and processor are loaded once during application startup.
Reference image metadata is polled from Spring on each analysis; new, changed,
and deleted references update the in-memory embedding cache. Explicitly rebuild
the cache with `POST /reference-images/refresh`. Spring serves metadata and
image bytes from its existing reference-image storage APIs; the ML service does
not connect to PostgreSQL or invent storage paths. Similarity indicates visual
resemblance only and does not establish product authenticity.

The visual assessment compares the identified product against its own cached
reference images. ORB feature matches plus RANSAC homography align images before
structural similarity and HSV color-distribution comparison. OCR tokens are
compared with reference product text; decoded barcode evidence is reported
separately. Logo comparison is performed only when a reference is tagged
`LOGO`. Unalignable images and missing evidence return unavailable fields, not
invented scores. Normal photographic variation can make the result inconclusive.

`LIKELY_GENUINE` and `SUSPICIOUS` are disabled unless
`VISUAL_DETECTION_CALIBRATED=true`; the default outcome is always
`INCONCLUSIVE`. The calibration switch is an operator assertion, not an
automatic validation. Before enabling it, use a representative, held-out set of
known genuine and counterfeit images across products, packaging variants,
lighting, camera angles, rotation, and image quality. Choose the thresholds
below from measured false-positive/false-negative tradeoffs, document the
dataset and results, and re-check them whenever the reference collection or
pipeline changes. The repository currently contains no labeled validation
dataset, and no accuracy claim is made.
`overallConfidence` is an evidence-strength score derived from the displayed
signals, not a calibrated probability.

Configurable calibration values (all thresholds are provisional unless measured
on that validation set):

| Environment variable | Default | Purpose |
| --- | ---: | --- |
| `VISUAL_DETECTION_CALIBRATED` | `false` | Explicitly enable preliminary classification after calibration |
| `VISUAL_MIN_IMAGE_DIMENSION` | `160` | Minimum width/height |
| `VISUAL_MIN_BLUR_SCORE` | `35` | Minimum preprocessing sharpness score |
| `VISUAL_MIN_REFERENCE_IMAGES` | `2` | Minimum cached references for a product |
| `VISUAL_MAX_REFERENCES_PER_REGION` | `3` | Maximum reference views compared per evidence region |
| `VISUAL_MIN_CLIP_SIMILARITY` | `0.72` | Minimum CLIP score for consistency |
| `VISUAL_MIN_IDENTIFICATION_CONFIDENCE` | `0.7` | Minimum product-identification score |
| `VISUAL_MIN_OCR_CONFIDENCE` | `0.8` | OCR confidence included in text comparison |
| `VISUAL_MIN_OCR_REGIONS_FOR_DETECTION` | `3` | Minimum confident OCR regions for text-only concern |
| `VISUAL_MIN_ALIGNMENT_INLIERS` | `8` | Minimum RANSAC inliers |
| `VISUAL_MIN_ALIGNMENT_RATIO` | `0.25` | Minimum inlier ratio |
| `VISUAL_MIN_OVERLAP_RATIO` | `0.2` | Minimum aligned image overlap |
| `VISUAL_CONSISTENT_SSIM` | `0.78` | Structural consistency threshold |
| `VISUAL_SUSPICIOUS_SSIM` | `0.45` | Structural discrepancy threshold |
| `VISUAL_CONSISTENT_COLOR_SIMILARITY` | `0.72` | Color consistency threshold |
| `VISUAL_SUSPICIOUS_COLOR_SIMILARITY` | `0.4` | Color discrepancy threshold |
| `VISUAL_MAX_OCR_MISSING_RATIO` | `0.25` | Expected OCR token missing-ratio threshold |
| `VISUAL_REGION_SSIM_THRESHOLD` | `0.45` | Per-region structural difference threshold |

These are configuration defaults, not asserted validated operating points.

Spring's reference-image operations are:

- `GET /api/ml/reference-images` for the reference inventory.
- `GET /api/ml/reference-images/{imageId}/content` for stored image bytes.
- `PUT /api/images/{imageId}/content` to replace an existing reference image.

Newly uploaded, replaced, and deleted references are detected on the next
analysis request. Use the ML refresh endpoint to rebuild the complete cache
immediately.

## Integration with the backend

See [API_CONTRACT.md](API_CONTRACT.md) for the image-upload, extraction, and visual-match contract. Start the ML service, then run the live multipart smoke test from this directory:

```powershell
.\venv\Scripts\python.exe scripts\smoke_test.py
```
