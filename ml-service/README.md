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
- `POST /analyze` accepts this JSON request:

  ```json
  {
    "product_name": "AirPods Pro",
    "brand": "Apple",
    "price": 24999
  }
  ```

  It returns the following fixed dummy response with HTTP 200:

  ```json
  {
    "product_name": "AirPods Pro",
    "brand": "Apple",
    "price": 24999,
    "verdict": "SUSPICIOUS",
    "confidence": 0.5,
    "reasons": ["Dummy response: real analysis is not implemented yet"],
    "analysis_mode": "dummy"
  }
  ```

  Invalid input returns HTTP 422. `/analyze` is a **DUMMY** endpoint; real analysis arrives on Days 6-10. Example PowerShell request:

  ```powershell
  curl.exe -X POST http://127.0.0.1:8000/analyze -H "Content-Type: application/json" -d '{"product_name":"AirPods Pro","brand":"Apple","price":24999}'
  ```

`/predict` currently uses hard-coded demo reference data for AirPods Pro and iPhone 15. No trained model exists yet.

## Integration with the backend

See [API_CONTRACT.md](API_CONTRACT.md) for the backend request and response contract. Start the ML service, then run the live smoke test from this directory:

```powershell
.\venv\Scripts\python.exe scripts\smoke_test.py
```
