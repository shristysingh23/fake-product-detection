# ML Service API Contract

## Base URL

Use `http://127.0.0.1:8000`. In Spring Boot configuration, use `127.0.0.1` instead of `localhost`: this Uvicorn setup binds to IPv4 `127.0.0.1`, while `localhost` can resolve to IPv6 on Windows and fail to connect.

## Start and check the service

From the `ml-service` directory in PowerShell, start the service with the existing virtual environment:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check it with `GET http://127.0.0.1:8000/health`. A healthy service returns HTTP 200:

```json
{"status":"ok"}
```

## POST /analyze

- Method: `POST`
- URL: `http://127.0.0.1:8000/analyze`
- Header: `Content-Type: application/json`

Request fields and validation:

| Field | Type | Validation |
| --- | --- | --- |
| `product_name` | string | Required; must be non-empty after trimming surrounding whitespace. |
| `brand` | string | Required; must be non-empty after trimming surrounding whitespace. |
| `price` | number | Required; must be greater than zero. |

Valid request example:

```json
{
  "product_name": "AirPods Pro",
  "brand": "Apple",
  "price": 24999
}
```

## Success response

HTTP 200 example captured from the running service:

```json
{
  "product_name": "AirPods Pro",
  "brand": "Apple",
  "price": 24999.0,
  "verdict": "SUSPICIOUS",
  "confidence": 0.5,
  "reasons": [
    "Dummy response: real analysis is not implemented yet"
  ],
  "analysis_mode": "dummy"
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `product_name` | string | Validated product name echoed from the request. |
| `brand` | string | Validated brand echoed from the request. |
| `price` | number | Validated price echoed from the request. |
| `verdict` | string | Current placeholder verdict. |
| `confidence` | number | Current placeholder confidence, between 0 and 1. |
| `reasons` | array of strings | Explanations associated with the verdict. |
| `analysis_mode` | string | Identifies the current response mode. |

`analysis_mode` is currently `"dummy"`. Response values will change when real analysis arrives; field names will stay the same unless the team agrees to change them.

## Error response

Invalid input returns HTTP 422. Example captured from the running service for `price: -5`:

```json
{"detail":[{"type":"greater_than","loc":["body","price"],"msg":"Input should be greater than 0","input":-5,"ctx":{"gt":0.0}}]}
```

The backend should treat any non-200 status as an error.

## Java mapping hint

Suggested Java types for JSON fields:

| JSON field | Suggested Java type |
| --- | --- |
| `product_name` | `String` |
| `brand` | `String` |
| `price` | `double` |
| `verdict` | `String` |
| `confidence` | `double` |
| `reasons` | `List<String>` |
| `analysis_mode` | `String` |

## Suggested HTTP client timeouts

Suggested timeout values are 3 seconds to connect and 10 seconds to read. These are suggestions because later analysis may take longer.

## Questions for the backend team

- Can you confirm these field names?
- Will images be sent later?
- Who handles retry and error mapping?
