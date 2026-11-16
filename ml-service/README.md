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
- `POST /analyze` accepts one `image` file as `multipart/form-data` (JPEG, PNG, or WebP). It returns the placeholder brand, product, and status plus OCR text and confidence lines. Unsupported types, empty files, and unreadable images return HTTP 400; a missing image part returns HTTP 422; unexpected OCR failures return HTTP 503. See [API_CONTRACT.md](API_CONTRACT.md) for the full contract.

## Running with OCR

Set `OCR_PRELOAD=1` to load OCR models when the service starts, then start Uvicorn:

```powershell
$env:OCR_PRELOAD="1"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Manually check `/analyze` with a JPEG image:

```powershell
curl.exe -F "image=@C:\path\to\photo.jpg;type=image/jpeg" http://127.0.0.1:8000/analyze
```


`/predict` currently uses hard-coded demo reference data for AirPods Pro and iPhone 15. No trained model exists yet.

## Integration with the backend

See [API_CONTRACT.md](API_CONTRACT.md) for the image-upload request and dummy response contract. Start the ML service, then run the live multipart smoke test from this directory:

```powershell
.\venv\Scripts\python.exe scripts\smoke_test.py
```

## Image preprocessing (Day 6)

The `app/preprocessing.py` module decodes image bytes, resizes large images, trims plain uniform borders, and reduces noise. The pipeline order is decode → resize → trim borders → reduce noise; the images remain uint8 BGR for OCR and YOLO, with a separate helper for normalized float output.

Run the demo with an image path and, optionally, an output folder (default: `ml-service/output`):

```powershell
.\venv\Scripts\python.exe scripts\preprocess_demo.py path\to\product.png [output-folder]
```

This preprocessing pipeline is not yet used by `/analyze`.

## Text extraction / OCR (Day 7)

`app/ocr.py` detects text regions in an image, then recognizes the characters in each region. Each returned line includes its text, confidence score, and four-corner box. Confidence is a model estimate, not proof that the text is correct.

PaddleOCR loads lazily on the first OCR call and downloads its models on first use (internet access is needed once). The pinned stack is `numpy==2.3.5`, `opencv-contrib-python==4.10.0.84`, `paddlepaddle==3.2.0`, `paddleocr==3.7.0`, and `paddlex==3.7.2`. Only one OpenCV package may be installed: PaddleX requires `opencv-contrib-python`, so `opencv-python-headless` must not be installed alongside it.

Run the demo from `ml-service` with preprocessing, or pass `--raw` to skip it:

```powershell
.\venv\Scripts\python.exe scripts\ocr_demo.py path\to\product.jpg
.\venv\Scripts\python.exe scripts\ocr_demo.py path\to\product.jpg --raw
```

To run the real OCR integration test in PowerShell:

```powershell
$env:RUN_OCR_INTEGRATION="1"
.\venv\Scripts\python.exe -m pytest -v tests\test_ocr.py
```

### Windows troubleshooting

Importing Paddle creates a folder under the user's home directory (`C:\Users\<you>\.cache\paddle`, taken from `USERPROFILE`). If that location is not writable, create a writable folder and set `USERPROFILE` to it for that terminal only; never run Git in that terminal.

OCR is not yet used by `/analyze`.
