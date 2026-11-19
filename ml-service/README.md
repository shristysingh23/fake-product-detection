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
- `POST /analyze` accepts one `image` file as `multipart/form-data` (JPEG, PNG, or WebP). It validates and preprocesses the image, extracts OCR text, and matches the OCR lines against the validated product catalog. It returns one of `IDENTIFIED`, `AMBIGUOUS`, or `NOT_FOUND`, plus the OCR text and confidence lines. Unsupported types, empty files, and unreadable images return HTTP 400; a missing image part returns HTTP 422; OCR, catalog, or matcher service failures return HTTP 503. See [API_CONTRACT.md](API_CONTRACT.md) for the exact response.

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

See [API_CONTRACT.md](API_CONTRACT.md) for the image-upload request and response contract. Start the ML service, then run the live multipart smoke test from this directory:

```powershell
.\venv\Scripts\python.exe scripts\smoke_test.py
```

## Image preprocessing (Day 6)

The `app/preprocessing.py` module decodes image bytes, resizes large images, trims plain uniform borders, and reduces noise. The pipeline order is decode → resize → trim borders → reduce noise; the images remain uint8 BGR for OCR and YOLO, with a separate helper for normalized float output.

Run the demo with an image path and, optionally, an output folder (default: `ml-service/output`):

```powershell
.\venv\Scripts\python.exe scripts\preprocess_demo.py path\to\product.png [output-folder]
```

This preprocessing pipeline is used by `/analyze` before OCR.

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

OCR output is passed to the product matcher by `/analyze`; the API preserves the extracted text and per-line OCR confidence.

## Product reference catalog

`data/products.json` is the versioned product reference catalog used by the matcher. It uses a top-level `schema_version` and a `products` array. Each product record requires a unique non-empty `product_id`, canonical `brand` and `product_name`, a string-or-null `category`, and `brand_aliases` and `product_aliases` arrays of non-empty strings. The loader rejects malformed records and conflicting normalized aliases. FastAPI validates and caches the default catalog at startup; restart the service after catalog changes.

The initial entries are based on the three benchmark package images. Visible package text was used to establish exact displayed variants and categories; official manufacturer sources were consulted for corroboration where available. The Maggi benchmark OCR misread “2-Minute” but captured “Masala” and “Instant Noodles with Seasoning”; its `Masala Instant Noodles` alias combines those separate visible package phrases and is not an additional product claim.

| Product ID | Brand | Canonical product name | Category | Verification basis |
| --- | --- | --- | --- | --- |
| `maggi-2-minute-masala-noodles` | MAGGI | 2-Minute Masala Noodles | Instant Noodles | Package shows MAGGI, 2-Minute noodles, and Masala; [Nestlé India](https://www.nestle.in/nhw/nutri-treats/recipes/smart-snacking-on-the-go) uses “MAGGI 2-Minute Noodles (Masala)”. |
| `dove-daily-shine-shampoo` | Dove | Daily Shine Shampoo | Shampoo | Bottle shows Dove, Daily Shine, and Shampoo; [Dove](https://www.dove.com/id/stories/tips-and-how-to/hair-care-tips-advice/kembalikan-kilau-rambut-indahmu-dengan-dove-daily-shine.html) identifies Dove Daily Shine Shampoo. |
| `amul-pasteurised-butter` | Amul | Pasteurised Butter | Butter | Package shows Amul, Pasteurised, and Butter; [Amul’s official brochure](https://amul.com/files/pdf/HORECA_BROCHURE_21052024.pdf) lists Amul Butter. |

The `Masala Instant Noodles` alias is supported by the package’s separate “Masala” and “Instant Noodles with Seasoning” text, with the exact MAGGI Masala variant corroborated by Nestlé India. Other aliases are limited to useful package wording. No package size, OCR-confused code, barcode, or manufacturer identifier is being treated as a verified product identifier.

`app.text_normalization.normalize_text()` applies deterministic NFKC and case-folding, uses punctuation and special characters as token separators, and collapses whitespace. It preserves letters, digits, model-number components, and unit tokens. It does not perform spelling correction or product matching.

## OCR brand and product matching (Step 3)

`app.product_matcher.identify_product()` compares OCR line records with validated catalog brands, brand aliases, product names, and product aliases. `/analyze` passes it the lines returned by the existing OCR pipeline; no second OCR pipeline or hardcoded brand/product fallback is used.

Matching is deterministic. It uses token-level exact matches and conservative edit similarity for tokens of at least four characters (default similarity threshold 0.82). Product evidence down-weights generic words and requires at least one distinctive product token. Brand and product evidence are combined as `0.40 × brand score + 0.60 × product score`. Valid OCR confidence adjusts lexical scores by at most five percent; missing or invalid confidence is neutral and cannot supply missing product evidence.

Initial configurable thresholds are provisional starting values, not validated accuracy claims: review score 0.70, brand score 0.80, product score 0.72, combined identification score 0.82, and winning margin 0.06. They require evaluation against a verified, representative catalog and labeled images before operational use.

- `IDENTIFIED`: brand, product, and combined scores meet their thresholds, and the leading candidate clears the required margin.
- `AMBIGUOUS`: at least one candidate reaches the review score, but the identification conditions are not all met. Product is left empty; brand is returned only when plausible candidates share it.
- `NOT_FOUND`: no candidate reaches review. A uniquely supported brand may still be returned.

These outcomes describe catalog text matching only. OCR confidence and identification do not verify whether a product is genuine or counterfeit. The validated catalog is loaded and cached during FastAPI startup; an empty catalog is valid, while missing or invalid catalog data fails startup. Catalog loading and validation errors are raised, not converted into `NOT_FOUND`.
