# ML Service API Contract

## Base URL

Use `http://127.0.0.1:8000`. In Spring Boot configuration, use `127.0.0.1` instead of `localhost`: Uvicorn here binds to IPv4 `127.0.0.1`, while `localhost` can resolve to IPv6 on Windows and fail to connect.

## Start and check the service

From the `ml-service` directory in PowerShell, start the service with the existing virtual environment:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `GET http://127.0.0.1:8000/health`. A healthy service returns HTTP 200:

```json
{"status":"ok"}
```

## Request: POST /analyze

- Method: `POST`
- URL: `http://127.0.0.1:8000/analyze`
- Content type: `multipart/form-data`
- Required file part name: `image` (exactly one file part)
- Accepted declared file content types: `image/jpeg`, `image/png`, and `image/webp`
- Maximum upload size: 10 MB (enforced by image preprocessing).

The endpoint validates the declared content type, rejects empty files, verifies
the image bytes, preprocesses the image, then runs OCR, barcode/QR detection, CLIP matching, and the explainable
preliminary visual assessment. The uploaded image is handled in memory and is
not saved to disk.

## Responses

### Success

HTTP 200:

```json
{
  "processingStatus": "COMPLETED",
  "extractedText": [{"text": "MAGGI", "confidence": 0.98}],
  "barcodes": [{"type": "EAN13", "value": "8901234567890"}],
  "qrCodes": [],
  "processingErrors": [],
  "preprocessing": {"originalDimensions":{"width":800,"height":600},"format":"PNG","orientationCorrected":true,"blurScore":300.0,"preprocessed":true},
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
    "identifiedProduct": null,
    "clipSimilarityScore": null,
    "logoComparison": {"status": "NOT_AVAILABLE"},
    "packagingComparison": {"status": "NOT_COMPARABLE"},
    "ocrDiscrepancies": {"status": "REFERENCE_TEXT_NOT_AVAILABLE"},
    "barcodeEvidence": {
      "status": "NOT_DETECTED",
      "observedValues": [],
      "expectedValue": null,
      "note": "A barcode match is not proof of authenticity."
    },
    "imageQuality": {
      "status": "ACCEPTABLE",
      "width": 800,
      "height": 600,
      "blurScore": 300.0,
      "issues": []
    },
    "suspiciousObservations": [],
    "referenceIssues": [],
    "explanation": "Insufficient evidence for a preliminary assessment."
  }
}
```

`visualDetection.outcome` is `LIKELY_GENUINE`, `SUSPICIOUS`, or
`INCONCLUSIVE`. Classification remains disabled by default until the operator
calibrates configurable thresholds using a representative labeled genuine and
counterfeit validation set and explicitly enables
`VISUAL_DETECTION_CALIBRATED=true`. The project has no such dataset; no accuracy
claim is made. CLIP similarity, barcode matches, and these preliminary outcomes
are not proof or certificates of authenticity. Comparison scores are null when
the relevant images could not be aligned or evidence was unavailable.

The legacy `brand`, `product`, and `status` fields remain for compatibility. `status` at the ML boundary is extraction-only and should not be interpreted as authenticity. Spring Boot performs reference matching and may replace it with `IDENTIFIED`, `MULTIPLE_MATCHES`, or `NOT_IDENTIFIED`.

`visualMatches` is ranked by descending cosine similarity between normalized
`openai/clip-vit-base-patch32` image embeddings. It contains the matched
`productId`, `referenceImageId`, and a `similarityScore` in `[-1, 1]`.
Similarity is not an authenticity probability.

Spring Boot exposes the existing local reference image bytes to the ML service:

- `GET /api/ml/reference-images` lists reference IDs, product IDs, content types,
  file sizes and high-resolution modification timestamps.
- `GET /api/ml/reference-images/{imageId}/content` returns one stored image.
- `PUT /api/images/{imageId}/content` replaces a reference image; its next
  inventory poll causes the ML service to regenerate that image embedding.

The ML service refreshes changed/deleted references while analyzing and supports
`POST /reference-images/refresh` to force a full embedding rebuild. Set
`REFERENCE_BACKEND_URL` to the Spring base URL if it differs from
`http://127.0.0.1:8080`.

### Unsupported file type

HTTP 400, captured for a `text/plain` upload (PDF and other unsupported declared content types return the same detail):

```json
{"detail":"Unsupported file type. Please upload a JPEG, PNG or WebP image."}
```

### Empty file

HTTP 400, captured for an empty file declared as `image/png`:

```json
{"detail":"Uploaded file is empty."}
```

### Unreadable image

HTTP 400, captured for random bytes declared as `image/png`:

```json
{"detail":"Uploaded file is not a valid image."}
```

### Missing image part

HTTP 422, captured when the request has no image part:

```json
{"detail":[{"type":"missing","loc":["body","image"],"msg":"Field required","input":null}]}
```

The backend should treat any non-200 status as an error and map validation, upload, and connection errors appropriately.

## Java mapping hint

| JSON field | Suggested Java type |
| --- | --- |
| `brand` | `String` |
| `product` | `String` |
| `status` | `String` |
| `visualMatches` | List of product ID, reference image ID, and cosine similarity |
| `visualDetection` | Preliminary evidence result; see above |

## Suggested HTTP client timeouts

Suggested values are 3 seconds to connect and 30 seconds to read, because later analysis will take longer.
