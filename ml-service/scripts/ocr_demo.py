r"""Day 7 demo: run (preprocessing +) OCR on one image and print the text lines.

Usage, from the ml-service folder:
   .\venv\Scripts\python.exe scripts\ocr_demo.py path\to\product.jpg
   .\venv\Scripts\python.exe scripts\ocr_demo.py path\to\product.jpg --raw
   .\venv\Scripts\python.exe scripts\ocr_demo.py path\to\product.jpg --min-confidence 0.3

Run it with and without --raw and compare: does preprocessing help OCR?
The first run downloads the OCR models and can take several minutes.
Results are saved as JSON in ml-service\output (ignored by Git).
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Make "app" importable when this script is run from the scripts folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ocr import DEFAULT_MIN_CONFIDENCE, extract_text, ocr_result_to_dict  # noqa: E402
from app.preprocessing import decode_image, preprocess_image  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OCR on one product image.")
    parser.add_argument("image_path", help="path to a JPEG, PNG or WebP image")
    parser.add_argument("--raw", action="store_true", help="skip preprocessing, OCR the decoded original")
    parser.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE)
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "output"),
        help="where to save the JSON result",
    )
    args = parser.parse_args()

    path = Path(args.image_path)
    if not path.is_file():
        print(f"Image file not found: {path}")
        return 1

    data = path.read_bytes()
    try:
        if args.raw:
            image = decode_image(data)
            mode = "raw"
        else:
            image = preprocess_image(data).image
            mode = "preprocessed"
    except ValueError as error:
        print(f"Could not read image: {error}")
        return 1

    print(f"Running OCR on the {mode} image (first run downloads models; this can take a while)...")
    start = time.perf_counter()
    result = extract_text(image, min_confidence=args.min_confidence)
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"Lines found: {len(result.lines)}  (min confidence {args.min_confidence})")
    for line in result.lines:
        print(f"  {line.confidence:.2f}  {line.text}")
    print(f"OCR time: {elapsed_ms:.0f} ms (includes model loading on the first call)")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{path.stem}_ocr_{mode}.json"
    output_path.write_text(json.dumps(ocr_result_to_dict(result), indent=2), encoding="utf-8")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
