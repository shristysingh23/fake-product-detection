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

The endpoint validates the declared content type, rejects empty files, then checks that Pillow can read and verify the uploaded image. The uploaded bytes are handled in memory and are not saved to disk.

## Responses

### Success

HTTP 200 response captured from the running service using a valid PNG upload:

```json
{"brand":"MAGGI","product":"2-Minute Noodles","status":"ANALYSIS_PENDING"}
```

All three response fields are strings. These values are dummy placeholders and will gain fields later; the plan's Day 14 report adds similarity scores and issues. The field names `brand`, `product`, and `status` will not change without team agreement.

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

Suggested values are 3 seconds to connect and 30 seconds to read, because later analysis will take longer.

## Questions for the backend team

- Can you confirm the multipart part name `image`?
- Can you confirm the response field names `brand`, `product`, and `status`?
- How will Spring Boot map 400, 422, and connection errors?
