"""Evaluate real OCR plus catalog matching on originals and derived variants.

Run from the repository root or ``ml-service`` with the project virtual
environment. Originals are never changed. Derived files and reports are
created only when their destinations do not already exist.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from importlib import metadata
import json
from pathlib import Path
import sys
import time
from typing import Any

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.analysis import run_ocr_on_bytes
from app.catalog import get_product_catalog
from app.ocr import get_ocr_engine
from app.product_matcher import DEFAULT_CONFIG, MatchOutcome, identify_product
from app.text_normalization import normalize_text


VARIANT_DIR = SERVICE_ROOT / "test-images" / "evaluation-variants"
JSON_REPORT = SERVICE_ROOT / "output" / "product_evaluation.json"
MARKDOWN_REPORT = SERVICE_ROOT / "EVALUATION_REPORT.md"
GROUND_TRUTH = {
    "maggi.jpg": {"brand": "MAGGI", "product": "2-Minute Masala Noodles"},
    "dove.webp": {"brand": "Dove", "product": "Daily Shine Shampoo"},
    "amul.jpg": {"brand": "Amul", "product": "Pasteurised Butter"},
}
VARIANT_SPECS = (
    ("reduced_resolution", "Scale to 50% width and height using LANCZOS."),
    ("mild_blur", "Gaussian blur radius 0.6 pixels."),
    ("moderate_blur", "Gaussian blur radius 1.3 pixels."),
    ("brightness_low", "Brightness factor 0.85."),
    ("contrast_low", "Contrast factor 0.80."),
    ("small_rotation", "Rotate +4 degrees, bicubic resampling, white fill."),
    ("moderate_rotation", "Rotate -10 degrees, bicubic resampling, white fill."),
    ("partial_crop", "Crop 8% from each edge, retaining the central 84%."),
)


def _variants(image: Image.Image) -> dict[str, tuple[Image.Image, dict[str, Any]]]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    return {
        "reduced_resolution": (
            rgb.resize((max(1, width // 2), max(1, height // 2)), Image.Resampling.LANCZOS),
            {"scale": 0.5, "resampling": "LANCZOS"},
        ),
        "mild_blur": (rgb.filter(ImageFilter.GaussianBlur(0.6)), {"radius_pixels": 0.6}),
        "moderate_blur": (rgb.filter(ImageFilter.GaussianBlur(1.3)), {"radius_pixels": 1.3}),
        "brightness_low": (ImageEnhance.Brightness(rgb).enhance(0.85), {"factor": 0.85}),
        "contrast_low": (ImageEnhance.Contrast(rgb).enhance(0.80), {"factor": 0.80}),
        "small_rotation": (
            rgb.rotate(4, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white"),
            {"degrees": 4, "resampling": "BICUBIC", "fill": "white"},
        ),
        "moderate_rotation": (
            rgb.rotate(-10, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white"),
            {"degrees": -10, "resampling": "BICUBIC", "fill": "white"},
        ),
        "partial_crop": (
            rgb.crop((int(width * 0.08), int(height * 0.08),
                      int(width * 0.92), int(height * 0.92))),
            {"edge_fraction_removed": 0.08, "retained_fraction_each_axis": 0.84},
        ),
    }


def _prepare_images(*, reuse_existing_variants: bool, overwrite_reports: bool) -> list[dict[str, Any]]:
    originals: list[dict[str, Any]] = []
    for filename in GROUND_TRUTH:
        path = SERVICE_ROOT / "test-images" / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required benchmark image is missing: {path}")
        with Image.open(path) as image:
            image.verify()
        originals.append({
            "path": path,
            "filename": filename,
            "image_type": "original",
            "source_image": filename,
            "transformation": None,
            "expected": GROUND_TRUTH[filename],
        })

    derived: list[dict[str, Any]] = []
    variants_to_write: list[tuple[Path, Image.Image]] = []
    for original in originals:
        with Image.open(original["path"]) as source:
            generated = _variants(source)
        for variant_name, (variant_image, parameters) in generated.items():
            filename = f"{Path(original['filename']).stem}__{variant_name}.png"
            path = VARIANT_DIR / filename
            variants_to_write.append((path, variant_image))
            derived.append({
                "path": path,
                "filename": filename,
                "image_type": "derived",
                "source_image": original["filename"],
                "transformation": {"name": variant_name, "parameters": parameters},
                "expected": original["expected"],
            })

    collisions = [(path, image) for path, image in variants_to_write if path.exists()]
    if collisions and not reuse_existing_variants:
        raise FileExistsError(
            "Refusing to overwrite existing evaluation variants: "
            + ", ".join(str(path) for path, _ in collisions)
        )
    for path, expected_image in collisions:
        try:
            with Image.open(path) as existing:
                same = (
                    existing.size == expected_image.size
                    and ImageChops.difference(
                        existing.convert("RGB"), expected_image.convert("RGB")
                    ).getbbox() is None
                )
        except OSError:
            same = False
        if not same:
            raise FileExistsError(
                f"Existing evaluation variant differs from deterministic output: {path}"
            )
    if (JSON_REPORT.exists() or MARKDOWN_REPORT.exists()) and not overwrite_reports:
        existing = [str(path) for path in (JSON_REPORT, MARKDOWN_REPORT) if path.exists()]
        raise FileExistsError(
            "Refusing to overwrite existing evaluation report(s): " + ", ".join(existing)
        )

    VARIANT_DIR.mkdir(parents=True, exist_ok=True)
    for path, variant_image in variants_to_write:
        if not path.exists():
            variant_image.save(path, format="PNG", optimize=False)
        variant_image.close()
    return originals + derived


def _package_versions() -> dict[str, str | None]:
    versions = {}
    for package in ("paddleocr", "paddlex", "paddlepaddle", "Pillow"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _evaluate_image(item: dict[str, Any], engine: Any, catalog: tuple[Any, ...]) -> dict[str, Any]:
    total_start = time.perf_counter()
    row: dict[str, Any] = {
        "filename": item["filename"],
        "image_type": item["image_type"],
        "source_image": item["source_image"],
        "transformation": item["transformation"],
        "path": str(item["path"]),
        "format": None,
        "dimensions": None,
        "expected_brand": item["expected"]["brand"],
        "expected_product": item["expected"]["product"],
        "predicted_brand": "",
        "predicted_product": "",
        "predicted_status": None,
        "correct_brand": False,
        "correct_product": False,
        "correct_identification": False,
        "extracted_text": None,
        "ocr_line_count": 0,
        "average_ocr_confidence": None,
        # Includes the production preprocessing performed inside run_ocr_on_bytes.
        "preprocessing_and_ocr_seconds": None,
        "matcher_seconds": None,
        "total_processing_seconds": None,
        "error": None,
    }
    try:
        image_bytes = item["path"].read_bytes()
        with Image.open(item["path"]) as image:
            row["format"] = image.format
            row["dimensions"] = {"width": image.width, "height": image.height}
            image.verify()

        ocr_start = time.perf_counter()
        ocr_result = run_ocr_on_bytes(image_bytes, engine=engine)
        row["preprocessing_and_ocr_seconds"] = round(time.perf_counter() - ocr_start, 4)
        row["extracted_text"] = ocr_result.full_text
        row["ocr_lines"] = [
            {"text": line.text, "confidence": line.confidence}
            for line in ocr_result.lines
        ]
        row["ocr_line_count"] = len(ocr_result.lines)
        if ocr_result.lines:
            row["average_ocr_confidence"] = round(
                sum(line.confidence for line in ocr_result.lines) / len(ocr_result.lines), 6
            )

        matcher_start = time.perf_counter()
        match = identify_product(ocr_result.lines, catalog)
        row["matcher_seconds"] = round(time.perf_counter() - matcher_start, 6)
        row["predicted_brand"] = match.brand or ""
        row["predicted_product"] = match.product or ""
        row["predicted_status"] = match.outcome.value
        row["correct_brand"] = row["predicted_brand"].casefold() == row["expected_brand"].casefold()
        row["correct_product"] = (
            row["predicted_status"] == MatchOutcome.IDENTIFIED.value
            and row["predicted_product"].casefold() == row["expected_product"].casefold()
        )
        row["correct_identification"] = row["correct_brand"] and row["correct_product"]
    except Exception as error:
        row["error"] = f"{type(error).__name__}: {error}"
    finally:
        row["total_processing_seconds"] = round(time.perf_counter() - total_start, 4)
    return row


def _run_negative_cases(catalog: tuple[Any, ...]) -> list[dict[str, Any]]:
    cases = (
        ("unrelated_text", ["garden trowel", "stainless steel"], "NOT_FOUND"),
        ("brand_only", ["Maggi"], "NOT_FOUND"),
        ("generic_product_words", ["MAGGI", "original premium product"], "NOT_FOUND"),
        (
            "conflicting_product_evidence",
            ["MAGGI Masala Instant Noodles", "Dove Daily Shine Shampoo"],
            "AMBIGUOUS",
        ),
        ("similar_unsupported_name", ["Dove Daily Shine Conditioner"], "AMBIGUOUS"),
    )
    results = []
    for name, texts, expected_status in cases:
        match = identify_product(
            [{"text": text, "confidence": 0.95} for text in texts], catalog
        )
        false_identification = match.outcome is MatchOutcome.IDENTIFIED
        results.append({
            "case": name,
            "evaluation_type": "synthetic matcher-only negative; not a real image/OCR run",
            "ocr_text_input": texts,
            "expected_status": expected_status,
            "predicted_status": match.outcome.value,
            "predicted_brand": match.brand,
            "predicted_product": match.product,
            "false_product_identification": false_identification,
            "expectation_met": match.outcome.value == expected_status,
        })
    return results


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _timing_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(rows),
        "correct_identifications": sum(row["correct_identification"] for row in rows),
        "not_found": sum(row["predicted_status"] == MatchOutcome.NOT_FOUND.value for row in rows),
        "ambiguous": sum(row["predicted_status"] == MatchOutcome.AMBIGUOUS.value for row in rows),
        "average_preprocessing_and_ocr_seconds": _average([
            row["preprocessing_and_ocr_seconds"] for row in rows
            if row["preprocessing_and_ocr_seconds"] is not None
        ]),
        "average_total_processing_seconds": _average([
            row["total_processing_seconds"] for row in rows
            if row["total_processing_seconds"] is not None
        ]),
    }


def _result_analysis(rows: list[dict[str, Any]], catalog: tuple[Any, ...]) -> dict[str, Any]:
    variations: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row["image_type"] == "derived":
            name = row["transformation"]["name"]
            variations.setdefault(name, []).append(row)

    missed = []
    for row in rows:
        if row["correct_identification"]:
            continue
        record = next((item for item in catalog
                       if item.brand.casefold() == row["expected_brand"].casefold()
                       and item.product_name.casefold() == row["expected_product"].casefold()), None)
        observed_tokens = set(normalize_text(row.get("extracted_text") or "").split())
        phrases = ([record.product_name, *record.product_aliases] if record else [])
        best_phrase = max(phrases, key=lambda phrase: len(
            set(normalize_text(phrase).split()) & observed_tokens
        ), default=row["expected_product"])
        phrase_tokens = set(normalize_text(best_phrase).split())
        visible_terms = sorted(phrase_tokens & observed_tokens)
        missing_terms = sorted(phrase_tokens - observed_tokens)
        missed.append({
            "filename": row["filename"],
            "predicted_status": row["predicted_status"],
            "predicted_brand": row["predicted_brand"],
            "best_supported_catalog_phrase": best_phrase,
            "phrase_tokens_seen_in_ocr": visible_terms,
            "phrase_tokens_missing_from_ocr": missing_terms,
            "interpretation": (
                "OCR retained insufficient distinguishing product wording; this miss is "
                "consistent with loss of image text evidence and does not support lowering thresholds."
                if missing_terms else
                "The expected phrase tokens appear in OCR text; inspect alias coverage and matcher behavior."
            ),
        })

    return {
        "missed_image_identifications": missed,
        "derived_per_transformation": {
            name: _timing_summary(group) for name, group in sorted(variations.items())
        },
    }


def _build_report(*, reuse_existing_variants: bool, overwrite_reports: bool) -> dict[str, Any]:
    items = _prepare_images(
        reuse_existing_variants=reuse_existing_variants,
        overwrite_reports=overwrite_reports,
    )
    catalog = get_product_catalog()
    config = asdict(DEFAULT_CONFIG)
    init_start = time.perf_counter()
    engine = None
    initialization_error = None
    try:
        engine = get_ocr_engine()
    except Exception as error:
        initialization_error = f"{type(error).__name__}: {error}"
    initialization_seconds = round(time.perf_counter() - init_start, 4)

    if engine is None:
        image_results = []
        for item in items:
            result = _evaluate_image_without_engine(item, initialization_error)
            image_results.append(result)
    else:
        image_results = [_evaluate_image(item, engine, catalog) for item in items]

    originals = [row for row in image_results if row["image_type"] == "original"]
    derived = [row for row in image_results if row["image_type"] == "derived"]
    successful = [row for row in image_results if row["error"] is None]
    confidences = [
        line["confidence"]
        for row in successful
        for line in row.get("ocr_lines", [])
        if isinstance(line.get("confidence"), (int, float))
    ]
    negative_results = _run_negative_cases(catalog)
    summary = {
        "total_images_evaluated": len(image_results),
        "original_images_evaluated": len(originals),
        "derived_images_evaluated": len(derived),
        "additional_independent_real_images": 0,
        "correct_product_identifications": sum(row["correct_identification"] for row in image_results),
        "incorrect_product_identifications": sum(
            row["predicted_status"] == MatchOutcome.IDENTIFIED.value
            and not row["correct_identification"] for row in image_results
        ),
        "not_found_outcomes": sum(row["predicted_status"] == MatchOutcome.NOT_FOUND.value for row in image_results),
        "ambiguous_outcomes": sum(row["predicted_status"] == MatchOutcome.AMBIGUOUS.value for row in image_results),
        "brand_identifications_correct": sum(row["correct_brand"] for row in image_results),
        "product_identifications_correct": sum(row["correct_product"] for row in image_results),
        "average_ocr_confidence_across_recognized_lines": _average(confidences),
        "average_preprocessing_and_ocr_seconds": _average([
            row["preprocessing_and_ocr_seconds"] for row in successful
            if row["preprocessing_and_ocr_seconds"] is not None
        ]),
        "average_total_processing_seconds": _average([
            row["total_processing_seconds"] for row in image_results
            if row["total_processing_seconds"] is not None
        ]),
        "original_exact_match_successes": sum(row["correct_identification"] for row in originals),
        "original_exact_match_rate": (
            round(sum(row["correct_identification"] for row in originals) / len(originals), 4)
            if originals else None
        ),
        "derived_exact_match_successes": sum(row["correct_identification"] for row in derived),
        "derived_exact_match_rate": (
            round(sum(row["correct_identification"] for row in derived) / len(derived), 4)
            if derived else None
        ),
        "original_timing_and_outcomes": _timing_summary(originals),
        "derived_timing_and_outcomes": _timing_summary(derived),
        "negative_cases_evaluated": len(negative_results),
        "negative_false_product_identifications": sum(
            row["false_product_identification"] for row in negative_results
        ),
        "negative_expectations_met": sum(row["expectation_met"] for row in negative_results),
    }
    return {
        "evaluation": "real PaddleOCR and production matcher on original and deterministic derived images",
        "image_pipeline": "production run_ocr_on_bytes with production preprocessing, then identify_product",
        "catalog_record_count": len(catalog),
        "catalog_product_ids": [record.product_id for record in catalog],
        "ground_truth": GROUND_TRUTH,
        "model_initialization_seconds": initialization_seconds,
        "model_initialization_error": initialization_error,
        "engine": "real PaddleOCR via app.ocr.get_ocr_engine",
        "package_versions": _package_versions(),
        "thresholds": config,
        "image_variation_specs": [
            {"name": name, "description": description}
            for name, description in VARIANT_SPECS
        ],
        "results": image_results,
        "negative_matcher_only_results": negative_results,
        "image_result_analysis": _result_analysis(image_results, catalog),
        "summary": summary,
        "interpretation_limitations": [
            "Only three independent real product images were available; derived variants are not independent samples.",
            "Identification success rates describe this small benchmark only and are not general accuracy estimates.",
            "Negative cases use synthetic OCR text and do not count as image-pipeline evaluations.",
            "OCR confidence is a model confidence score, not recognition accuracy or authenticity evidence.",
            "IDENTIFIED, AMBIGUOUS, and NOT_FOUND describe catalog text matching, not product authenticity.",
        ],
    }


def _evaluate_image_without_engine(item: dict[str, Any], error: str | None) -> dict[str, Any]:
    return {
        "filename": item["filename"],
        "image_type": item["image_type"],
        "source_image": item["source_image"],
        "transformation": item["transformation"],
        "path": str(item["path"]),
        "format": None,
        "dimensions": None,
        "expected_brand": item["expected"]["brand"],
        "expected_product": item["expected"]["product"],
        "predicted_brand": "",
        "predicted_product": "",
        "predicted_status": None,
        "correct_brand": False,
        "correct_product": False,
        "correct_identification": False,
        "extracted_text": None,
        "ocr_lines": [],
        "ocr_line_count": 0,
        "average_ocr_confidence": None,
        "preprocessing_and_ocr_seconds": None,
        "matcher_seconds": None,
        "total_processing_seconds": None,
        "error": f"PaddleOCR initialization failed: {error}",
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Real-Image Product Identification Evaluation",
        "",
        "## Scope and method",
        "",
        "The evaluation ran the real cached PaddleOCR engine through the production `run_ocr_on_bytes` path (including production preprocessing), then passed its actual OCR lines to the production product matcher. No fake OCR output was used for image-pipeline results.",
        "",
        f"Catalog records loaded: **{report['catalog_record_count']}**. Model initialization: **{report['model_initialization_seconds']} seconds**. Initialization error: **{report['model_initialization_error']}**.",
        "",
        f"Package versions: `{json.dumps(report['package_versions'], sort_keys=True)}`",
        "",
        "The originals are the three supplied real benchmark photographs. The derived images are deterministic synthetic variations saved under `test-images/evaluation-variants/`; they are not independent real-world samples. No additional independent real product images were found.",
        "",
        "## Current matcher thresholds",
        "",
        "These are the existing provisional thresholds. They were not changed or calibrated by this evaluation.",
        "",
        "| Setting | Value |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in report["thresholds"].items())
    lines += [
        "",
        "## Image results",
        "",
        "| Filename | Type | Expected product | Predicted product | Status | Exact identification | OCR lines | Mean OCR confidence | Preprocess + OCR (s) | Total (s) | Error |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["results"]:
        lines.append(
            f"| {row['filename']} | {row['image_type']} | {row['expected_brand']} / {row['expected_product']} | "
            f"{row['predicted_brand']} / {row['predicted_product']} | {row['predicted_status']} | "
            f"{row['correct_identification']} | {row['ocr_line_count']} | {row['average_ocr_confidence']} | "
            f"{row['preprocessing_and_ocr_seconds']} | {row['total_processing_seconds']} | {row['error'] or ''} |"
        )
    lines += [
        "",
        "## Summary",
        "",
        f"- Total image evaluations: {summary['total_images_evaluated']} ({summary['original_images_evaluated']} originals, {summary['derived_images_evaluated']} derived; {summary['additional_independent_real_images']} additional independent real images).",
        f"- Correct exact product identifications: {summary['correct_product_identifications']}; incorrect product identifications: {summary['incorrect_product_identifications']}.",
        f"- NOT_FOUND: {summary['not_found_outcomes']}; AMBIGUOUS: {summary['ambiguous_outcomes']}.",
        f"- Brand identifications correct: {summary['brand_identifications_correct']}; product identifications correct: {summary['product_identifications_correct']}.",
        f"- Average OCR confidence across recognized lines: {summary['average_ocr_confidence_across_recognized_lines']}.",
        f"- Average preprocessing + OCR time: {summary['average_preprocessing_and_ocr_seconds']} seconds; average total time: {summary['average_total_processing_seconds']} seconds.",
        f"- Original exact-match result: {summary['original_exact_match_successes']}/{summary['original_images_evaluated']} ({summary['original_exact_match_rate']}).",
        f"- Derived variation exact-match result: {summary['derived_exact_match_successes']}/{summary['derived_images_evaluated']} ({summary['derived_exact_match_rate']}).",
        "",
        "The original and derived results are reported separately. Rates are descriptive results for this small sample, not general accuracy estimates.",
        "",
        "### Processing by image type",
        "",
        "| Type | Images | Exact identifications | NOT_FOUND | AMBIGUOUS | Average preprocess + OCR (s) | Average total (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, key in (("Original real images", "original_timing_and_outcomes"),
                       ("Derived variations", "derived_timing_and_outcomes")):
        group = summary[key]
        lines.append(
            f"| {label} | {group['count']} | {group['correct_identifications']} | {group['not_found']} | "
            f"{group['ambiguous']} | {group['average_preprocessing_and_ocr_seconds']} | "
            f"{group['average_total_processing_seconds']} |"
        )
    lines += [
        "",
        "### Derived results by transformation",
        "",
        "| Transformation | Images | Exact identifications | NOT_FOUND | AMBIGUOUS | Average preprocess + OCR (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, group in report["image_result_analysis"]["derived_per_transformation"].items():
        lines.append(
            f"| {name} | {group['count']} | {group['correct_identifications']} | {group['not_found']} | "
            f"{group['ambiguous']} | {group['average_preprocessing_and_ocr_seconds']} |"
        )
    lines += ["", "### Missed image identifications", ""]
    for missed in report["image_result_analysis"]["missed_image_identifications"]:
        lines.append(
            f"- `{missed['filename']}`: status `{missed['predicted_status']}`, brand `{missed['predicted_brand']}`; "
            f"catalog phrase `{missed['best_supported_catalog_phrase']}`. OCR saw tokens "
            f"{missed['phrase_tokens_seen_in_ocr']} and missed {missed['phrase_tokens_missing_from_ocr']}. "
            f"{missed['interpretation']}"
        )
    if not report["image_result_analysis"]["missed_image_identifications"]:
        lines.append("No original or derived image identification was missed.")
    lines += [
        "",
        "## Matcher-only negative cases",
        "",
        "These use synthetic OCR text directly with the matcher. They are separate from real image/OCR evaluation.",
        "",
        "| Case | Expected status | Predicted status | Predicted product | False product identification | Expectation met |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in report["negative_matcher_only_results"]:
        lines.append(
            f"| {row['case']} | {row['expected_status']} | {row['predicted_status']} | "
            f"{row['predicted_product']} | {row['false_product_identification']} | {row['expectation_met']} |"
        )
    lines += [
        "",
        f"Negative-test false product identifications: **{summary['negative_false_product_identifications']} / {summary['negative_cases_evaluated']}**.",
        "",
        "## OCR observations and threshold recommendation",
        "",
        "The misses are reported above with the catalog phrase tokens present and absent from OCR text. Product cues missing from OCR indicate an upstream image/OCR evidence limitation; if all cues are present but the matcher misses, the issue would instead point to catalog aliases or matching behavior. The OCR output remains available for every row in the JSON report.",
        "",
        "Only three independent product images are available, and the derived transforms are controlled variations of those same photographs. Keep the current thresholds: this dataset is too small and unrepresentative to justify calibration or claims of optimized performance. Collect additional independently photographed, labeled examples—including difficult lighting, angles, and similar variants—before recalibrating.",
        "",
        "## Limitations",
        "",
        "- OCR confidence is not recognition accuracy.",
        "- Derived variants do not increase the independent sample size.",
        "- Synthetic matcher-only negatives do not measure real-world false-positive rates.",
        "- Product identification is catalog text matching, not authenticity verification; no result establishes that a product is genuine or counterfeit.",
        "- Full extracted text, line-level confidence, transformations, errors, and timings are preserved in `output/product_evaluation.json`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-existing-variants",
        action="store_true",
        help="Reuse existing derived images only when they pixel-match deterministic output.",
    )
    parser.add_argument(
        "--overwrite-reports",
        action="store_true",
        help="Explicitly replace existing Step 6 JSON/Markdown reports.",
    )
    parser.add_argument(
        "--refresh-report-from-json",
        action="store_true",
        help="Recalculate analysis/Markdown from the existing JSON without rerunning OCR.",
    )
    args = parser.parse_args()
    if args.refresh_report_from_json:
        if not JSON_REPORT.is_file():
            print(f"Evaluation JSON report not found: {JSON_REPORT}", file=sys.stderr)
            return 2
        report = json.loads(JSON_REPORT.read_text(encoding="utf-8"))
        catalog = get_product_catalog()
        originals = [row for row in report["results"] if row["image_type"] == "original"]
        derived = [row for row in report["results"] if row["image_type"] == "derived"]
        report["summary"]["original_timing_and_outcomes"] = _timing_summary(originals)
        report["summary"]["derived_timing_and_outcomes"] = _timing_summary(derived)
        report["image_result_analysis"] = _result_analysis(report["results"], catalog)
        JSON_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        MARKDOWN_REPORT.write_text(_render_markdown(report), encoding="utf-8")
        print("Refreshed analysis from saved OCR results; no OCR was run.")
        return 0
    # Refuse report collisions before generating image files.
    if (JSON_REPORT.exists() or MARKDOWN_REPORT.exists()) and not args.overwrite_reports:
        existing = [str(path) for path in (JSON_REPORT, MARKDOWN_REPORT) if path.exists()]
        print("Refusing to overwrite existing evaluation report(s): " + ", ".join(existing), file=sys.stderr)
        return 2
    try:
        report = _build_report(
            reuse_existing_variants=args.reuse_existing_variants,
            overwrite_reports=args.overwrite_reports,
        )
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as error:
        print(f"Evaluation could not start: {type(error).__name__}: {error}", file=sys.stderr)
        return 2

    # Use exclusive creation as a final guard against concurrent overwrites.
    JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    try:
        report_mode = "w" if args.overwrite_reports else "x"
        with JSON_REPORT.open(report_mode, encoding="utf-8", newline="\n") as target:
            json.dump(report, target, indent=2, ensure_ascii=False)
            target.write("\n")
        with MARKDOWN_REPORT.open(report_mode, encoding="utf-8", newline="\n") as target:
            target.write(_render_markdown(report))
    except FileExistsError as error:
        print(f"Refusing to overwrite existing report: {error.filename}", file=sys.stderr)
        return 2

    print(json.dumps(report["summary"], indent=2))
    print(f"JSON report: {JSON_REPORT}")
    print(f"Markdown report: {MARKDOWN_REPORT}")
    print(f"Derived images: {VARIANT_DIR}")
    return 0 if all(row["error"] is None for row in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
