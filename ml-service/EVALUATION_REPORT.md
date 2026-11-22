# Real-Image Product Identification Evaluation

## Scope and method

The evaluation ran the real cached PaddleOCR engine through the production `run_ocr_on_bytes` path (including production preprocessing), then passed its actual OCR lines to the production product matcher. No fake OCR output was used for image-pipeline results.

Catalog records loaded: **3**. Model initialization: **13.273 seconds**. Initialization error: **None**.

Package versions: `{"Pillow": "12.3.0", "paddleocr": "3.7.0", "paddlepaddle": "3.2.0", "paddlex": "3.7.2"}`

The originals are the three supplied real benchmark photographs. The derived images are deterministic synthetic variations saved under `test-images/evaluation-variants/`; they are not independent real-world samples. No additional independent real product images were found.

## Current matcher thresholds

These are the existing provisional thresholds. They were not changed or calibrated by this evaluation.

| Setting | Value |
|---|---:|
| `brand_weight` | 0.4 |
| `product_weight` | 0.6 |
| `minimum_review_score` | 0.7 |
| `minimum_brand_score` | 0.8 |
| `minimum_product_score` | 0.72 |
| `minimum_identification_score` | 0.82 |
| `minimum_winning_margin` | 0.06 |
| `fuzzy_token_similarity` | 0.82 |

## Image results

| Filename | Type | Expected product | Predicted product | Status | Exact identification | OCR lines | Mean OCR confidence | Preprocess + OCR (s) | Total (s) | Error |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| maggi.jpg | original | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 34 | 0.933927 | 34.7148 | 34.7362 |  |
| dove.webp | original | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.916664 | 10.2295 | 10.2388 |  |
| amul.jpg | original | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 8 | 0.895359 | 15.1545 | 15.1594 |  |
| maggi__reduced_resolution.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 19 | 0.912416 | 21.7159 | 21.7331 |  |
| maggi__mild_blur.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 30 | 0.922628 | 36.6656 | 36.6946 |  |
| maggi__moderate_blur.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 18 | 0.935053 | 26.742 | 26.7605 |  |
| maggi__brightness_low.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 34 | 0.947008 | 38.9024 | 38.9294 |  |
| maggi__contrast_low.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 33 | 0.937252 | 36.8563 | 36.8825 |  |
| maggi__small_rotation.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 34 | 0.939984 | 37.842 | 37.8739 |  |
| maggi__moderate_rotation.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI / 2-Minute Masala Noodles | IDENTIFIED | True | 33 | 0.95242 | 37.0142 | 37.0461 |  |
| maggi__partial_crop.png | derived | MAGGI / 2-Minute Masala Noodles | MAGGI /  | NOT_FOUND | False | 27 | 0.928167 | 28.9534 | 28.9723 |  |
| dove__reduced_resolution.png | derived | Dove / Daily Shine Shampoo | Dove /  | NOT_FOUND | False | 1 | 0.999982 | 1.7689 | 1.7734 |  |
| dove__mild_blur.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 9 | 0.936585 | 8.9325 | 8.9394 |  |
| dove__moderate_blur.png | derived | Dove / Daily Shine Shampoo | Dove /  | NOT_FOUND | False | 1 | 0.999971 | 2.9147 | 2.9177 |  |
| dove__brightness_low.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.923983 | 10.5198 | 10.5286 |  |
| dove__contrast_low.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.92608 | 10.5933 | 10.6024 |  |
| dove__small_rotation.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.910831 | 12.7344 | 12.7446 |  |
| dove__moderate_rotation.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.893185 | 11.7022 | 11.713 |  |
| dove__partial_crop.png | derived | Dove / Daily Shine Shampoo | Dove / Daily Shine Shampoo | IDENTIFIED | True | 11 | 0.959184 | 12.3885 | 12.399 |  |
| amul__reduced_resolution.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 4 | 0.998963 | 5.3974 | 5.4025 |  |
| amul__mild_blur.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 6 | 0.918249 | 10.5015 | 10.5097 |  |
| amul__moderate_blur.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 4 | 0.999858 | 8.738 | 8.7434 |  |
| amul__brightness_low.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 9 | 0.894726 | 15.9359 | 15.9458 |  |
| amul__contrast_low.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 9 | 0.856982 | 13.8852 | 13.8909 |  |
| amul__small_rotation.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 10 | 0.849328 | 15.9928 | 16.0029 |  |
| amul__moderate_rotation.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 4 | 0.999977 | 10.3632 | 10.3706 |  |
| amul__partial_crop.png | derived | Amul / Pasteurised Butter | Amul / Pasteurised Butter | IDENTIFIED | True | 8 | 0.895359 | 13.7202 | 13.7448 |  |

## Summary

- Total image evaluations: 27 (3 originals, 24 derived; 0 additional independent real images).
- Correct exact product identifications: 24; incorrect product identifications: 0.
- NOT_FOUND: 3; AMBIGUOUS: 0.
- Brand identifications correct: 27; product identifications correct: 24.
- Average OCR confidence across recognized lines: 0.929.
- Average preprocessing + OCR time: 18.1807 seconds; average total time: 18.1946 seconds.
- Original exact-match result: 3/3 (1.0).
- Derived variation exact-match result: 21/24 (0.875).

The original and derived results are reported separately. Rates are descriptive results for this small sample, not general accuracy estimates.

### Processing by image type

| Type | Images | Exact identifications | NOT_FOUND | AMBIGUOUS | Average preprocess + OCR (s) | Average total (s) |
|---|---:|---:|---:|---:|---:|---:|
| Original real images | 3 | 3 | 0 | 0 | 20.0329 | 20.0448 |
| Derived variations | 24 | 21 | 3 | 0 | 17.9492 | 17.9634 |

### Derived results by transformation

| Transformation | Images | Exact identifications | NOT_FOUND | AMBIGUOUS | Average preprocess + OCR (s) |
|---|---:|---:|---:|---:|---:|
| brightness_low | 3 | 3 | 0 | 0 | 21.786 |
| contrast_low | 3 | 3 | 0 | 0 | 20.4449 |
| mild_blur | 3 | 3 | 0 | 0 | 18.6999 |
| moderate_blur | 3 | 2 | 1 | 0 | 12.7982 |
| moderate_rotation | 3 | 3 | 0 | 0 | 19.6932 |
| partial_crop | 3 | 2 | 1 | 0 | 18.354 |
| reduced_resolution | 3 | 2 | 1 | 0 | 9.6274 |
| small_rotation | 3 | 3 | 0 | 0 | 22.1897 |

### Missed image identifications

- `maggi__partial_crop.png`: status `NOT_FOUND`, brand `MAGGI`; catalog phrase `2-Minute Masala Noodles`. OCR saw tokens ['masala'] and missed ['2', 'minute', 'noodles']. OCR retained insufficient distinguishing product wording; this miss is consistent with loss of image text evidence and does not support lowering thresholds.
- `dove__reduced_resolution.png`: status `NOT_FOUND`, brand `Dove`; catalog phrase `Daily Shine Shampoo`. OCR saw tokens [] and missed ['daily', 'shampoo', 'shine']. OCR retained insufficient distinguishing product wording; this miss is consistent with loss of image text evidence and does not support lowering thresholds.
- `dove__moderate_blur.png`: status `NOT_FOUND`, brand `Dove`; catalog phrase `Daily Shine Shampoo`. OCR saw tokens [] and missed ['daily', 'shampoo', 'shine']. OCR retained insufficient distinguishing product wording; this miss is consistent with loss of image text evidence and does not support lowering thresholds.

## Matcher-only negative cases

These use synthetic OCR text directly with the matcher. They are separate from real image/OCR evaluation.

| Case | Expected status | Predicted status | Predicted product | False product identification | Expectation met |
|---|---|---|---|---:|---:|
| unrelated_text | NOT_FOUND | NOT_FOUND |  | False | True |
| brand_only | NOT_FOUND | NOT_FOUND |  | False | True |
| generic_product_words | NOT_FOUND | NOT_FOUND |  | False | True |
| conflicting_product_evidence | AMBIGUOUS | AMBIGUOUS |  | False | True |
| similar_unsupported_name | AMBIGUOUS | AMBIGUOUS |  | False | True |

Negative-test false product identifications: **0 / 5**.

## OCR observations and threshold recommendation

The misses are reported above with the catalog phrase tokens present and absent from OCR text. Product cues missing from OCR indicate an upstream image/OCR evidence limitation; if all cues are present but the matcher misses, the issue would instead point to catalog aliases or matching behavior. The OCR output remains available for every row in the JSON report.

Only three independent product images are available, and the derived transforms are controlled variations of those same photographs. Keep the current thresholds: this dataset is too small and unrepresentative to justify calibration or claims of optimized performance. Collect additional independently photographed, labeled examples—including difficult lighting, angles, and similar variants—before recalibrating.

## Limitations

- OCR confidence is not recognition accuracy.
- Derived variants do not increase the independent sample size.
- Synthetic matcher-only negatives do not measure real-world false-positive rates.
- Product identification is catalog text matching, not authenticity verification; no result establishes that a product is genuine or counterfeit.
- Full extracted text, line-level confidence, transformations, errors, and timings are preserved in `output/product_evaluation.json`.
