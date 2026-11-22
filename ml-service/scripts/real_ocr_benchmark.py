"""Benchmark real PaddleOCR on product photographs using the ML service pipeline.

Run from ``ml-service`` with image paths, or place supported files in
``test-images``. This script never substitutes a fake OCR engine.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import sys
import time
from typing import Any

from PIL import Image, UnidentifiedImageError

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.analysis import run_ocr_on_bytes
from app.ocr import get_ocr_engine

DEFAULT_IMAGE_DIR = SERVICE_ROOT / "test-images"
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def _load_image(path: Path) -> tuple[bytes, dict[str, Any]]:
    """Read and validate one supported image without changing its bytes."""
    metadata: dict[str, Any] = {
        "filename": path.name,
        "path": str(path),
        "format": None,
        "dimensions": None,
    }
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported extension {path.suffix!r}; use JPG, JPEG, PNG, or WebP."
        )

    data = path.read_bytes()
    with Image.open(BytesIO(data)) as image:
        image_format = image.format
        metadata["format"] = image_format
        metadata["dimensions"] = {
            "width": image.width,
            "height": image.height,
        }
        image.verify()

    if image_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format {image_format!r}; use JPEG, PNG, or WebP."
        )
    return data, metadata


def _result_record(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        **metadata,
        "extracted_text": None,
        "lines": [],
        "confidence_scores": [],
        "processing_time_seconds": None,
        "success": False,
        "error": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the real PaddleOCR engine on product images through the "
            "production preprocessing and OCR pipeline."
        )
    )
    parser.add_argument(
        "images",
        nargs="*",
        type=Path,
        help="Image paths; if omitted, supported images are read from test-images/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path. Existing files are not overwritten.",
    )
    args = parser.parse_args()

    image_paths = args.images or sorted(
        path
        for path in DEFAULT_IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not image_paths:
        parser.error(
            f"No product images supplied or found in {DEFAULT_IMAGE_DIR}. "
            "Add photographs or pass their paths explicitly."
        )
    if args.output is not None and args.output.exists():
        parser.error(f"Refusing to overwrite existing report: {args.output}")

    results: list[dict[str, Any]] = []
    pending: list[tuple[Path, bytes, dict[str, Any], dict[str, Any]]] = []
    for path in image_paths:
        record = _result_record({
            "filename": path.name,
            "path": str(path),
            "format": None,
            "dimensions": None,
        })
        try:
            data, metadata = _load_image(path)
            record.update(metadata)
            pending.append((path, data, metadata, record))
        except (OSError, UnidentifiedImageError, ValueError) as error:
            record["error"] = f"{type(error).__name__}: {error}"
        results.append(record)

    initialization_seconds: float | None = None
    initialization_error: str | None = None
    engine = None
    if pending:
        start = time.perf_counter()
        try:
            engine = get_ocr_engine()
        except Exception as error:
            initialization_error = f"{type(error).__name__}: {error}"
        initialization_seconds = time.perf_counter() - start

    if engine is None:
        for _, _, _, record in pending:
            record["error"] = f"PaddleOCR initialization failed: {initialization_error}"
    else:
        for path, data, _, record in pending:
            start = time.perf_counter()
            try:
                # Uses the production preprocessing path and the real cached/downloaded engine.
                result = run_ocr_on_bytes(data, engine=engine)
                record["extracted_text"] = result.full_text
                record["lines"] = [
                    {"text": line.text, "confidence": line.confidence}
                    for line in result.lines
                ]
                record["confidence_scores"] = [
                    line.confidence for line in result.lines
                ]
                record["success"] = True
            except Exception as error:
                record["error"] = f"{type(error).__name__}: {error}"
            finally:
                record["processing_time_seconds"] = round(
                    time.perf_counter() - start, 3
                )

    report = {
        "engine": "real PaddleOCR via app.ocr.get_ocr_engine",
        "pipeline": "app.analysis.run_ocr_on_bytes with production preprocessing enabled",
        "model_initialization_seconds": (
            round(initialization_seconds, 3)
            if initialization_seconds is not None
            else None
        ),
        "model_initialization_error": initialization_error,
        "results": results,
        "summary": {
            "images": len(results),
            "succeeded": sum(record["success"] for record in results),
            "failed": sum(not record["success"] for record in results),
        },
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
