# Real OCR Test Report

## Environment and pipeline

- Platform: Windows 10; Python 3.12.6 in `ml-service/venv`.
- OCR stack: PaddleOCR 3.7.0, PaddleX 3.7.2, PaddlePaddle 3.2.0.
- Engine: real PaddleOCR, configured with `lang="en"`; this selects PP-OCRv6 medium text detection and recognition models (`PP-OCRv6_medium_det` and `PP-OCRv6_medium_rec`).
- Pipeline: `app.analysis.run_ocr_on_bytes` with production preprocessing enabled. The production confidence filter is 0.5. No OCR or preprocessing parameters were changed for this benchmark.
- Model initialization: **27.891 seconds**; initialization error: none.
- Per-image processing times below are the values recorded by the benchmark. Model initialization is reported separately.

The benchmark JSON records successful execution, extracted lines, scores, dimensions, and timing. Installed environment versions and model selection were checked against the project virtual environment and current production configuration.

## Results

### Maggi — `maggi.jpg`

- Format: JPEG
- Dimensions: 733 × 1000 pixels
- Processing time: **43.445 seconds**
- Success: **Yes**
- Average OCR confidence: **0.933927** across 34 lines

Complete extracted text (lines in OCR output order):

```text
Maggi
ASI
R
2mMinuts
22 KARAT
CHANCE TO
WiN A GOLD BOWL
WORTH 5 LAKHS eVeRY WeeK
emasala taste
Win Gold Vouchers worth 2000 Every Hour
Your FavouRiTe
ruly
MADE WiTH
GOOD
QUALiTY SPiCES*
& GOODNESS OF iRON
If a serve is 70 g (1 pack)
indore
Energy
ToalFatSaTSSom
SUGGESTED GARNISHING
269 kcal
8.8 g
5.8 g 1.3 g
700.0mg
13%
13%
29%
1%29%
Masala
关
% of Guideline Daily Amounts of an
average adult (2000 kcal)
Instant Noodles with Seasoning*
```

Confidence scores in the same line order (rounded to six decimals):

| # | OCR line | Confidence |
|---:|---|---:|
| 1 | Maggi | 0.999141 |
| 2 | ASI | 0.711918 |
| 3 | R | 0.950790 |
| 4 | 2mMinuts | 0.744042 |
| 5 | 22 KARAT | 0.993577 |
| 6 | CHANCE TO | 0.946885 |
| 7 | WiN A GOLD BOWL | 0.962651 |
| 8 | WORTH 5 LAKHS eVeRY WeeK | 0.902380 |
| 9 | emasala taste | 0.958387 |
| 10 | Win Gold Vouchers worth 2000 Every Hour | 0.979272 |
| 11 | Your FavouRiTe | 0.898452 |
| 12 | ruly | 0.996164 |
| 13 | MADE WiTH | 0.967098 |
| 14 | GOOD | 0.999886 |
| 15 | QUALiTY SPiCES* | 0.922632 |
| 16 | & GOODNESS OF iRON | 0.945509 |
| 17 | If a serve is 70 g (1 pack) | 0.973277 |
| 18 | indore | 0.960624 |
| 19 | Energy | 0.963999 |
| 20 | ToalFatSaTSSom | 0.691155 |
| 21 | SUGGESTED GARNISHING | 0.998769 |
| 22 | 269 kcal | 0.910442 |
| 23 | 8.8 g | 0.966106 |
| 24 | 5.8 g 1.3 g | 0.925398 |
| 25 | 700.0mg | 0.990335 |
| 26 | 13% | 0.999867 |
| 27 | 13% | 0.999873 |
| 28 | 29% | 0.990378 |
| 29 | 1%29% | 0.996291 |
| 30 | Masala | 0.999984 |
| 31 | 关 | 0.575186 |
| 32 | % of Guideline Daily Amounts of an | 0.999830 |
| 33 | average adult (2000 kcal) | 0.966046 |
| 34 | Instant Noodles with Seasoning* | 0.967161 |

### Dove — `dove.webp`

- Format: WebP
- Dimensions: 459 × 547 pixels
- Processing time: **10.738 seconds**
- Success: **Yes**
- Average OCR confidence: **0.916664** across 11 lines

Complete extracted text (lines in OCR output order):

```text
Dove
NUTRITIVE
SOLUTIONS
Daily
Shine
SHAMPOO
FORDULLHAIR
Nourpoemdaly
wear&tearandrestoresshine
180 ml
68354812
```

Confidence scores in the same line order (rounded to six decimals):

| # | OCR line | Confidence |
|---:|---|---:|
| 1 | Dove | 0.999994 |
| 2 | NUTRITIVE | 0.999929 |
| 3 | SOLUTIONS | 0.999783 |
| 4 | Daily | 0.998357 |
| 5 | Shine | 0.999872 |
| 6 | SHAMPOO | 0.999926 |
| 7 | FORDULLHAIR | 0.816510 |
| 8 | Nourpoemdaly | 0.522842 |
| 9 | wear&tearandrestoresshine | 0.818668 |
| 10 | 180 ml | 0.958685 |
| 11 | 68354812 | 0.968734 |

### Amul — `amul.jpg`

- Format: JPEG
- Dimensions: 1000 × 1000 pixels
- Processing time: **16.893 seconds**
- Success: **Yes**
- Average OCR confidence: **0.895359** across 8 lines

Complete extracted text (lines in OCR output order):

```text
Mik
Ltd
bddus
Amul
AE
PASTEURISED
BUTTER
utterly butterly delicious
```

Confidence scores in the same line order (rounded to six decimals):

| # | OCR line | Confidence |
|---:|---|---:|
| 1 | Mik | 0.817234 |
| 2 | Ltd | 0.945299 |
| 3 | bddus | 0.789967 |
| 4 | Amul | 0.999951 |
| 5 | AE | 0.610472 |
| 6 | PASTEURISED | 0.999985 |
| 7 | BUTTER | 0.999990 |
| 8 | utterly butterly delicious | 0.999972 |

## Summary and observations

| Total images | Succeeded | Failed |
|---:|---:|---:|
| 3 | 3 | 0 |

- The brand names “Maggi”, “Dove”, and “Amul” were present in the extracted text. The Maggi product wording was partly misread (`2mMinuts`); Amul also had short spurious lines (`Mik`, `Ltd`, `bddus`, `AE`).
- Dove’s prominent branding and product type were extracted, while smaller label text was merged or misrecognized (`Nourpoemdaly`, `wear&tearandrestoresshine`). Maggi included extensive package and nutrition text, with some garbled or combined lines.
- Success means the real OCR pipeline completed without an execution error. It does not mean every line is correct.
- OCR confidence is the model's confidence for each recognized line, not a measure of actual recognition accuracy. No ground-truth transcription or accuracy percentage was available or calculated. High confidence can still accompany incorrect text.
- This is a three-image sample. Results may vary with image quality, angle, glare, crop, and small print; this benchmark alone does not establish general accuracy.

Source data: `ml-service/output/real_ocr_benchmark.json` (preserved unchanged).
