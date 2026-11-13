# ML Service (FastAPI)

A FastAPI service for the Fake Product Detection project.

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

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
- `POST /predict` accepts `product_name` (string), `brand` (string), and `price` (number). It returns `product_name`, `brand`, `price`, and `prediction`.
- `POST /analyze` accepts one `image` file as `multipart/form-data` (JPEG, PNG, or WebP). It returns the dummy JSON `{"brand":"MAGGI","product":"2-Minute Noodles","status":"ANALYSIS_PENDING"}` with HTTP 200. Unsupported types, empty files, and unreadable images return HTTP 400; a missing image part returns HTTP 422. See [API_CONTRACT.md](API_CONTRACT.md) for the full contract.


`/predict` currently uses hard-coded demo reference data for AirPods Pro and iPhone 15. No trained model exists yet.

## Integration with the backend

See [API_CONTRACT.md](API_CONTRACT.md) for the image-upload request and dummy response contract. Start the ML service, then run the live multipart smoke test from this directory:

```powershell
.\venv\Scripts\python.exe scripts\smoke_test.py
```
