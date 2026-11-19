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
- Suggested maximum upload size: 10 MB as a team recommendation; the service does not enforce this limit yet.

The endpoint validates the declared content type, rejects empty files, then checks that Pillow can read and verify the uploaded image. The uploaded bytes are handled in memory and are not saved to disk. Processing then follows image preprocessing → PaddleOCR text extraction → catalog matching. OCR text and confidence are returned even when no product is identified.

The validated product catalog is loaded and cached once during application startup. An empty but valid catalog is supported. A missing or invalid catalog prevents startup; ASGI deployments that do not run lifespan receive HTTP 503 if the catalog cannot be loaded on request. Catalog configuration errors are not treated as no-match results.

## Responses

### Success

HTTP 200 response for a valid image upload:

```json
{
  "brand": "",
  "product": "",
  "status": "NOT_FOUND",
  "identification_source": "product_catalog",
  "extracted_text": "",
  "ocr_lines": []
}
```

| Name | Type | Meaning |
| --- | --- | --- |
| `brand` | string | Canonical matched brand, a uniquely supported brand for unresolved outcomes, or `""`. Never null. |
| `product` | string | Canonical product only for `IDENTIFIED`; otherwise `""`. Never null. |
| `status` | string | `IDENTIFIED`, `AMBIGUOUS`, or `NOT_FOUND`, as determined by catalog text matching. |
| `identification_source` | string | `product_catalog`. |
| `extracted_text` | string | Recognized text lines joined by newline characters; empty if no text was found. |
| `ocr_lines` | array of objects | Real OCR output, each with `text` (string) and `confidence` (number from 0 to 1). |

`IDENTIFIED` means the catalog matcher met its configured text-evidence thresholds. `AMBIGUOUS` means catalog candidates remain unresolved; product is empty, and brand is included only when plausible candidates share it. `NOT_FOUND` means no catalog candidate reached review; a uniquely supported brand may still be included. These statuses are not authenticity verification and do not establish that an item is genuine or counterfeit. OCR confidence is a model score, not proof that the text is correct. The six response fields and their types remain unchanged for the Spring Boot DTO.

The first request after server start takes much longer while OCR models load. The first call in a new process took about 40 to 60 seconds on the developer's laptop; warm-call time has not been measured. Start the service with `OCR_PRELOAD=1` to load models during startup, and use a backend client read timeout of at least 60 seconds.

If OCR fails unexpectedly, the service returns HTTP 503:

```json
{"detail":"Text extraction failed. Please try again."}
```

If product matching fails unexpectedly, the service returns HTTP 503 with `{"detail":"Product identification failed. Please try again."}`. If the catalog cannot be loaded outside startup, it returns HTTP 503 with `{"detail":"Product catalog is unavailable."}`. Internal errors are not included in either response.

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

## Suggested HTTP client timeouts

Use a 3-second connect timeout and a read timeout of at least 60 seconds for OCR model loading.

## Questions for the backend team

- Can you confirm the multipart part name `image`?
- Can you confirm the response field names `brand`, `product`, and `status`?
- How will Spring Boot map 400, 422, and connection errors?
