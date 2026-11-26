from dataclasses import dataclass
import os
import re

import cv2
import numpy as np
from PIL import Image

from app.visual_matching import CachedReference


_VARIABLE_LABEL_TOKENS = {
    "batch", "lot", "mfg", "manufactured", "expiry", "expires", "exp",
    "date", "mrp", "price", "net", "weight", "barcode", "serial",
}


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value.")


@dataclass(frozen=True)
class VisualDetectionConfig:
    calibrated: bool = False
    minimum_image_dimension: int = 160
    minimum_blur_score: float = 35.0
    minimum_reference_images: int = 2
    max_references_per_region: int = 3
    minimum_clip_similarity: float = 0.72
    minimum_identification_confidence: float = 0.7
    minimum_ocr_confidence: float = 0.8
    minimum_ocr_regions_for_detection: int = 3
    minimum_alignment_inliers: int = 8
    minimum_alignment_ratio: float = 0.25
    minimum_overlap_ratio: float = 0.2
    minimum_consistent_ssim: float = 0.78
    maximum_suspicious_ssim: float = 0.45
    minimum_consistent_color_similarity: float = 0.72
    maximum_suspicious_color_similarity: float = 0.4
    maximum_ocr_missing_ratio: float = 0.25
    region_ssim_threshold: float = 0.45

    def __post_init__(self):
        unit_interval_values = {
            "minimum_identification_confidence": self.minimum_identification_confidence,
            "minimum_ocr_confidence": self.minimum_ocr_confidence,
            "minimum_alignment_ratio": self.minimum_alignment_ratio,
            "minimum_overlap_ratio": self.minimum_overlap_ratio,
            "minimum_consistent_color_similarity": self.minimum_consistent_color_similarity,
            "maximum_suspicious_color_similarity": self.maximum_suspicious_color_similarity,
            "maximum_ocr_missing_ratio": self.maximum_ocr_missing_ratio,
            "region_ssim_threshold": self.region_ssim_threshold,
        }
        for name, value in unit_interval_values.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        if not -1 <= self.minimum_clip_similarity <= 1:
            raise ValueError("minimum_clip_similarity must be between -1 and 1.")
        if not -1 <= self.minimum_consistent_ssim <= 1:
            raise ValueError("minimum_consistent_ssim must be between -1 and 1.")
        if not -1 <= self.maximum_suspicious_ssim <= 1:
            raise ValueError("maximum_suspicious_ssim must be between -1 and 1.")
        if self.maximum_suspicious_ssim >= self.minimum_consistent_ssim:
            raise ValueError("Suspicious SSIM threshold must be below consistency threshold.")
        if self.maximum_suspicious_color_similarity >= self.minimum_consistent_color_similarity:
            raise ValueError("Suspicious color threshold must be below consistency threshold.")
        if self.minimum_image_dimension < 1 or self.minimum_blur_score < 0:
            raise ValueError("Image dimension and blur thresholds must be non-negative.")
        if self.minimum_reference_images < 1 or self.max_references_per_region < 1:
            raise ValueError("Reference image counts must be positive.")
        if self.minimum_ocr_regions_for_detection < 1 or self.minimum_alignment_inliers < 4:
            raise ValueError("OCR-region and alignment-inlier counts are too small.")

    @classmethod
    def from_environment(cls):
        return cls(
            calibrated=_env_bool("VISUAL_DETECTION_CALIBRATED", False),
            minimum_image_dimension=_env_int("VISUAL_MIN_IMAGE_DIMENSION", 160),
            minimum_blur_score=_env_float("VISUAL_MIN_BLUR_SCORE", 35.0),
            minimum_reference_images=_env_int("VISUAL_MIN_REFERENCE_IMAGES", 2),
            max_references_per_region=_env_int("VISUAL_MAX_REFERENCES_PER_REGION", 3),
            minimum_clip_similarity=_env_float("VISUAL_MIN_CLIP_SIMILARITY", 0.72),
            minimum_identification_confidence=_env_float(
                "VISUAL_MIN_IDENTIFICATION_CONFIDENCE", 0.7
            ),
            minimum_ocr_confidence=_env_float("VISUAL_MIN_OCR_CONFIDENCE", 0.8),
            minimum_ocr_regions_for_detection=_env_int(
                "VISUAL_MIN_OCR_REGIONS_FOR_DETECTION", 3
            ),
            minimum_alignment_inliers=_env_int("VISUAL_MIN_ALIGNMENT_INLIERS", 8),
            minimum_alignment_ratio=_env_float("VISUAL_MIN_ALIGNMENT_RATIO", 0.25),
            minimum_overlap_ratio=_env_float("VISUAL_MIN_OVERLAP_RATIO", 0.2),
            minimum_consistent_ssim=_env_float("VISUAL_CONSISTENT_SSIM", 0.78),
            maximum_suspicious_ssim=_env_float("VISUAL_SUSPICIOUS_SSIM", 0.45),
            minimum_consistent_color_similarity=_env_float(
                "VISUAL_CONSISTENT_COLOR_SIMILARITY", 0.72
            ),
            maximum_suspicious_color_similarity=_env_float(
                "VISUAL_SUSPICIOUS_COLOR_SIMILARITY", 0.4
            ),
            maximum_ocr_missing_ratio=_env_float("VISUAL_MAX_OCR_MISSING_RATIO", 0.25),
            region_ssim_threshold=_env_float("VISUAL_REGION_SSIM_THRESHOLD", 0.45),
        )


def _normal_tokens(text: str) -> set[str]:
    tokens = set()
    for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(token) < 3 or token.isdigit() or token in _VARIABLE_LABEL_TOKENS:
            continue
        tokens.add(token)
    return tokens


def _letterbox(image: np.ndarray, size: int = 640):
    height, width = image.shape[:2]
    scale = min(size / width, size / height)
    resized_width = max(1, round(width * scale))
    resized_height = max(1, round(height * scale))
    resized = cv2.resize(
        image,
        (resized_width, resized_height),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
    )
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    mask = np.zeros((size, size), dtype=np.uint8)
    x = (size - resized_width) // 2
    y = (size - resized_height) // 2
    canvas[y:y + resized_height, x:x + resized_width] = resized
    mask[y:y + resized_height, x:x + resized_width] = 255
    return canvas, mask


def _ssim_map(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left = left.astype(np.float32) / 255.0
    right = right.astype(np.float32) / 255.0
    mu_left = cv2.GaussianBlur(left, (11, 11), 1.5)
    mu_right = cv2.GaussianBlur(right, (11, 11), 1.5)
    mu_left_sq = mu_left * mu_left
    mu_right_sq = mu_right * mu_right
    mu_cross = mu_left * mu_right
    sigma_left = cv2.GaussianBlur(left * left, (11, 11), 1.5) - mu_left_sq
    sigma_right = cv2.GaussianBlur(right * right, (11, 11), 1.5) - mu_right_sq
    sigma_cross = cv2.GaussianBlur(left * right, (11, 11), 1.5) - mu_cross
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    numerator = (2 * mu_cross + c1) * (2 * sigma_cross + c2)
    denominator = (mu_left_sq + mu_right_sq + c1) * (
        sigma_left + sigma_right + c2
    )
    return np.clip(numerator / np.maximum(denominator, 1e-8), -1.0, 1.0)


def _suspicious_regions(ssim_map: np.ndarray, valid_mask: np.ndarray, config):
    changed = np.logical_and(
        ssim_map < config.region_ssim_threshold,
        valid_mask > 0,
    ).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, kernel)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(changed)
    height, width = changed.shape
    regions = []
    minimum_area = max(100, int(width * height * 0.002))
    for index in range(1, count):
        x, y, region_width, region_height, area = stats[index]
        if area < minimum_area:
            continue
        regions.append({
            "x": round(float(x) / width, 4),
            "y": round(float(y) / height, 4),
            "width": round(float(region_width) / width, 4),
            "height": round(float(region_height) / height, 4),
            "areaRatio": round(float(area) / (width * height), 4),
        })
    return sorted(regions, key=lambda region: region["areaRatio"], reverse=True)[:5]


def compare_aligned_images(query_bgr: np.ndarray, reference: Image.Image, config):
    reference_bgr = cv2.cvtColor(np.asarray(reference.convert("RGB")), cv2.COLOR_RGB2BGR)
    query_canvas, query_mask = _letterbox(query_bgr)
    reference_canvas, reference_mask = _letterbox(reference_bgr)
    query_gray = cv2.cvtColor(query_canvas, cv2.COLOR_BGR2GRAY)
    reference_gray = cv2.cvtColor(reference_canvas, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    query_gray = clahe.apply(query_gray)
    reference_gray = clahe.apply(reference_gray)

    orb = cv2.ORB_create(nfeatures=1600, scaleFactor=1.2, nlevels=8)
    reference_points, reference_descriptors = orb.detectAndCompute(reference_gray, reference_mask)
    query_points, query_descriptors = orb.detectAndCompute(query_gray, query_mask)
    if reference_descriptors is None or query_descriptors is None:
        return {"status": "NOT_COMPARABLE", "reason": "Insufficient image features for alignment."}

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(reference_descriptors, query_descriptors, k=2)
    good = [
        first
        for pair in pairs
        if len(pair) == 2
        for first, second in [pair]
        if first.distance < 0.75 * second.distance
    ]
    if len(good) < 4:
        return {"status": "NOT_COMPARABLE", "reason": "Images could not be aligned reliably."}

    source_points = np.float32(
        [reference_points[item.queryIdx].pt for item in good]
    ).reshape(-1, 1, 2)
    target_points = np.float32(
        [query_points[item.trainIdx].pt for item in good]
    ).reshape(-1, 1, 2)
    homography, inlier_mask = cv2.findHomography(
        source_points, target_points, cv2.RANSAC, 4.0
    )
    inlier_count = int(inlier_mask.sum()) if inlier_mask is not None else 0
    inlier_ratio = inlier_count / len(good)
    if (
        homography is None
        or inlier_count < config.minimum_alignment_inliers
        or inlier_ratio < config.minimum_alignment_ratio
    ):
        return {
            "status": "NOT_COMPARABLE",
            "reason": "Feature alignment confidence is insufficient.",
            "alignmentInliers": inlier_count,
            "alignmentInlierRatio": round(inlier_ratio, 4),
        }

    aligned_reference = cv2.warpPerspective(
        reference_canvas, homography, (query_canvas.shape[1], query_canvas.shape[0])
    )
    aligned_mask = cv2.warpPerspective(
        reference_mask, homography, (query_canvas.shape[1], query_canvas.shape[0])
    )
    valid_mask = cv2.bitwise_and(query_mask, aligned_mask)
    overlap_ratio = cv2.countNonZero(valid_mask) / cv2.countNonZero(query_mask)
    if overlap_ratio < config.minimum_overlap_ratio:
        return {
            "status": "NOT_COMPARABLE",
            "reason": "Aligned image overlap is insufficient.",
            "alignmentInliers": inlier_count,
            "alignmentInlierRatio": round(inlier_ratio, 4),
        }

    aligned_gray = clahe.apply(cv2.cvtColor(aligned_reference, cv2.COLOR_BGR2GRAY))
    similarity_map = _ssim_map(query_gray, aligned_gray)
    valid = valid_mask > 0
    structural_similarity = float(np.mean(similarity_map[valid]))

    query_hsv = cv2.cvtColor(query_canvas, cv2.COLOR_BGR2HSV)
    reference_hsv = cv2.cvtColor(aligned_reference, cv2.COLOR_BGR2HSV)
    color_similarities = []
    for channel, bins, value_range in (
        (0, 18, [0, 180]),
        (1, 8, [0, 256]),
    ):
        query_hist = cv2.calcHist(
            [query_hsv], [channel], valid_mask, [bins], value_range
        )
        reference_hist = cv2.calcHist(
            [reference_hsv], [channel], valid_mask, [bins], value_range
        )
        cv2.normalize(query_hist, query_hist, alpha=1, norm_type=cv2.NORM_L1)
        cv2.normalize(reference_hist, reference_hist, alpha=1, norm_type=cv2.NORM_L1)
        color_similarities.append(
            1.0 - cv2.compareHist(
                query_hist, reference_hist, cv2.HISTCMP_BHATTACHARYYA
            )
        )
    color_similarity = 0.8 * color_similarities[0] + 0.2 * color_similarities[1]

    return {
        "status": "COMPARABLE",
        "structuralSimilarity": round(structural_similarity, 4),
        "colorSimilarity": round(float(np.clip(color_similarity, 0.0, 1.0)), 4),
        "alignmentInliers": inlier_count,
        "alignmentInlierRatio": round(inlier_ratio, 4),
        "overlapRatio": round(overlap_ratio, 4),
        "suspiciousRegions": _suspicious_regions(
            similarity_map, valid_mask, config
        ),
    }


class VisualDetectionEngine:
    def __init__(self, config: VisualDetectionConfig | None = None, comparator=None):
        self.config = config or VisualDetectionConfig.from_environment()
        self._comparator = comparator or compare_aligned_images

    def analyze(
        self,
        image_bgr: np.ndarray,
        references: list[tuple[int, CachedReference]],
        visual_matches: list[dict],
        extracted_text: list[dict],
        barcodes: list[dict],
        qr_codes: list[dict],
        preprocessing: dict,
        reference_errors: list[str] | None = None,
    ) -> dict:
        reference_errors = reference_errors or []
        identified = self._identify_product(
            references, visual_matches, extracted_text, barcodes, qr_codes
        )
        product_id = identified["productId"] if identified else None
        product_references = [
            (reference_id, reference)
            for reference_id, reference in references
            if reference.product_id == product_id
        ] if product_id is not None else []
        clip_by_reference = {
            item["referenceImageId"]: item["similarityScore"]
            for item in visual_matches
        }
        clip_score = max(
            (
                clip_by_reference.get(reference_id)
                for reference_id, _ in product_references
                if clip_by_reference.get(reference_id) is not None
            ),
            default=None,
        )

        quality = self._quality(preprocessing)
        barcode_evidence = self._barcode_evidence(product_references, barcodes, qr_codes)
        text_evidence = self._text_evidence(product_references, extracted_text)
        packaging = self._compare_region(
            image_bgr,
            product_references,
            clip_by_reference,
            allowed_types={"FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM", "LABEL"},
        )
        logo = self._compare_region(
            image_bgr,
            product_references,
            clip_by_reference,
            allowed_types={"LOGO"},
        )

        observations = []
        for comparison in packaging["referencesCompared"] + logo["referencesCompared"]:
            for region in comparison.get("suspiciousRegions", []):
                observations.append({
                    "type": "STRUCTURAL_DIFFERENCE",
                    "referenceImageId": comparison["referenceImageId"],
                    "region": region,
                })
        if barcode_evidence["status"] == "MISMATCH":
            observations.append({
                "type": "BARCODE_MISMATCH",
                "description": "Decoded barcode differs from the selected reference product.",
            })
        if text_evidence["status"] == "DIFFERENCES_FOUND":
            observations.append({
                "type": "OCR_TEXT_DIFFERENCE",
                "description": "Some expected reference text was not read in the uploaded image.",
            })

        outcome, explanation, overall_confidence = self._decide(
            identified,
            product_references,
            clip_score,
            quality,
            packaging,
            logo,
            text_evidence,
            barcode_evidence,
            reference_errors,
        )
        return {
            "outcome": outcome,
            "overallConfidence": overall_confidence,
            "calibrationStatus": "CALIBRATED" if self.config.calibrated else "NOT_CALIBRATED",
            "identifiedProduct": identified,
            "clipSimilarityScore": clip_score,
            "logoComparison": logo,
            "packagingComparison": packaging,
            "ocrDiscrepancies": text_evidence,
            "barcodeEvidence": barcode_evidence,
            "imageQuality": quality,
            "suspiciousObservations": observations,
            "referenceIssues": reference_errors,
            "explanation": explanation,
        }

    def unavailable(self, explanation: str) -> dict:
        unavailable_comparison = {
            "status": "UNAVAILABLE",
            "structuralSimilarity": None,
            "colorSimilarity": None,
            "referencesCompared": [],
        }
        return {
            "outcome": "INCONCLUSIVE",
            "overallConfidence": None,
            "calibrationStatus": "CALIBRATED" if self.config.calibrated else "NOT_CALIBRATED",
            "identifiedProduct": None,
            "clipSimilarityScore": None,
            "logoComparison": dict(unavailable_comparison),
            "packagingComparison": dict(unavailable_comparison),
            "ocrDiscrepancies": {
                "status": "UNAVAILABLE",
                "mismatchRatio": None,
                "missingExpectedTokens": [],
                "unexpectedObservedTokens": [],
                "confidentRegions": 0,
            },
            "barcodeEvidence": {
                "status": "UNAVAILABLE",
                "observedValues": [],
                "expectedValue": None,
                "note": "Barcode evidence comparison was unavailable.",
            },
            "imageQuality": {
                "status": "UNAVAILABLE",
                "width": None,
                "height": None,
                "blurScore": None,
                "issues": [],
            },
            "suspiciousObservations": [],
            "referenceIssues": [],
            "explanation": explanation,
        }

    def _identify_product(self, references, visual_matches, extracted_text, barcodes, qr_codes):
        if not references:
            return None

        products = {}
        for reference_id, reference in references:
            products.setdefault(reference.product_id, []).append((reference_id, reference))

        observed_barcodes = {
            item.get("value", "").strip()
            for item in barcodes + qr_codes
            if item.get("value")
        }
        exact_barcode_products = {
            product_id
            for product_id, entries in products.items()
            if any(reference.barcode in observed_barcodes for _, reference in entries if reference.barcode)
        }
        if len(exact_barcode_products) == 1:
            selected = next(iter(exact_barcode_products))
            return self._product_identity(
                selected, products[selected], 1.0, "EXACT_BARCODE"
            )

        observed_text = " ".join(item.get("text", "") for item in extracted_text)
        observed_tokens = _normal_tokens(observed_text)
        text_candidates = []
        for product_id, entries in products.items():
            reference = entries[0][1]
            brand = _normal_tokens(reference.brand or "")
            product_name = _normal_tokens(reference.product_name or "")
            brand_match = bool(brand and brand.issubset(observed_tokens))
            product_match = bool(product_name and product_name.issubset(observed_tokens))
            if brand_match and product_match:
                text_candidates.append((product_id, 0.9, "OCR_BRAND_AND_PRODUCT"))
            elif product_match:
                text_candidates.append((product_id, 0.72, "OCR_PRODUCT_NAME"))
        if text_candidates:
            text_candidates.sort(key=lambda result: result[1], reverse=True)
            if len(text_candidates) == 1 or text_candidates[0][1] > text_candidates[1][1]:
                product_id, confidence, evidence = text_candidates[0]
                return self._product_identity(
                    product_id, products[product_id], confidence, evidence
                )

        per_product_clip = {}
        for match in visual_matches:
            product_id = match["productId"]
            per_product_clip[product_id] = max(
                per_product_clip.get(product_id, -1.0), match["similarityScore"]
            )
        ranked = sorted(per_product_clip.items(), key=lambda item: item[1], reverse=True)
        if not ranked:
            return None
        if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.03:
            return None
        product_id, score = ranked[0]
        if product_id not in products:
            return None
        return self._product_identity(product_id, products[product_id], score, "CLIP")

    def _product_identity(self, product_id, entries, confidence, evidence):
        reference = entries[0][1]
        return {
            "productId": product_id,
            "brand": reference.brand,
            "productName": reference.product_name,
            "identificationConfidence": round(float(confidence), 4),
            "identificationEvidence": evidence,
        }

    def _quality(self, preprocessing):
        dimensions = preprocessing.get("originalDimensions") or {}
        width = int(dimensions.get("width", 0))
        height = int(dimensions.get("height", 0))
        blur_score = float(preprocessing.get("blurScore", 0.0))
        reasons = []
        if min(width, height) < self.config.minimum_image_dimension:
            reasons.append("Image resolution is below the configured minimum.")
        if blur_score < self.config.minimum_blur_score:
            reasons.append("Image sharpness is below the configured minimum.")
        return {
            "status": "LOW" if reasons else "ACCEPTABLE",
            "width": width,
            "height": height,
            "blurScore": blur_score,
            "issues": reasons,
        }

    def _barcode_evidence(self, entries, barcodes, qr_codes):
        observed = [
            item.get("value", "")
            for item in barcodes + qr_codes
            if item.get("value")
        ]
        expected_values = {
            reference.barcode
            for _, reference in entries
            if reference.barcode
        }
        if not expected_values:
            status = "REFERENCE_NOT_AVAILABLE" if observed else "NOT_DETECTED"
            expected = None
        elif not observed:
            status = "NOT_DETECTED"
            expected = sorted(expected_values)[0]
        elif expected_values.intersection(observed):
            status = "MATCH"
            expected = sorted(expected_values)[0]
        else:
            status = "MISMATCH"
            expected = sorted(expected_values)[0]
        return {
            "status": status,
            "observedValues": observed,
            "expectedValue": expected,
            "note": "A barcode match is not proof of authenticity.",
        }

    def _text_evidence(self, entries, extracted_text):
        expected_candidates = []
        for _, reference in entries:
            expected = _normal_tokens(reference.expected_text or "")
            expected.update(_normal_tokens(reference.brand or ""))
            expected.update(_normal_tokens(reference.product_name or ""))
            if expected:
                expected_candidates.append(expected)
        observed = set()
        confident_regions = 0
        for item in extracted_text:
            if float(item.get("confidence") or 0.0) >= self.config.minimum_ocr_confidence:
                confident_regions += 1
                observed.update(_normal_tokens(item.get("text", "")))
        if not expected_candidates:
            return {
                "status": "REFERENCE_TEXT_NOT_AVAILABLE",
                "mismatchRatio": None,
                "missingExpectedTokens": [],
                "unexpectedObservedTokens": sorted(observed),
                "confidentRegions": confident_regions,
            }
        expected = min(
            expected_candidates,
            key=lambda candidate: len(candidate - observed) / len(candidate),
        )
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        mismatch_ratio = len(missing) / len(expected)
        if confident_regions == 0:
            status = "OCR_NOT_CONFIDENT"
        elif mismatch_ratio >= self.config.maximum_ocr_missing_ratio:
            status = "DIFFERENCES_FOUND"
        else:
            status = "NO_SIGNIFICANT_DIFFERENCE"
        return {
            "status": status,
            "mismatchRatio": round(mismatch_ratio, 4),
            "missingExpectedTokens": missing,
            "unexpectedObservedTokens": unexpected,
            "confidentRegions": confident_regions,
        }

    def _compare_region(self, image_bgr, entries, clip_by_reference, allowed_types):
        selected = [
            (reference_id, reference)
            for reference_id, reference in entries
            if reference.image_type in allowed_types
        ]
        selected.sort(
            key=lambda item: clip_by_reference.get(item[0], -1.0),
            reverse=True,
        )
        selected = selected[:self.config.max_references_per_region]
        if not selected:
            return {
                "status": "NOT_AVAILABLE",
                "structuralSimilarity": None,
                "colorSimilarity": None,
                "referencesCompared": [],
            }

        comparisons = []
        for reference_id, reference in selected:
            try:
                result = self._comparator(image_bgr, reference.image, self.config)
            except cv2.error:
                result = {
                    "status": "NOT_COMPARABLE",
                    "reason": "OpenCV could not align these images.",
                }
            result["referenceImageId"] = reference_id
            result["clipSimilarityScore"] = clip_by_reference.get(reference_id)
            comparisons.append(result)
        comparable = [
            result for result in comparisons if result.get("status") == "COMPARABLE"
        ]
        if not comparable:
            return {
                "status": "NOT_COMPARABLE",
                "structuralSimilarity": None,
                "colorSimilarity": None,
                "referencesCompared": comparisons,
            }

        best = max(comparable, key=lambda result: result["structuralSimilarity"])
        return {
            "status": "COMPARABLE",
            "structuralSimilarity": best["structuralSimilarity"],
            "colorSimilarity": best["colorSimilarity"],
            "bestReferenceImageId": best["referenceImageId"],
            "referencesCompared": comparisons,
        }

    def _decide(
        self, identified, entries, clip_score, quality, packaging, logo,
        text_evidence, barcode_evidence, reference_errors,
    ):
        if quality["status"] != "ACCEPTABLE":
            return "INCONCLUSIVE", "Uploaded image quality is insufficient for a reliable comparison.", None
        if identified is None or (
            identified["identificationConfidence"]
            < self.config.minimum_identification_confidence
        ):
            return "INCONCLUSIVE", "The product could not be identified with sufficient confidence.", None
        if len(entries) < self.config.minimum_reference_images:
            return "INCONCLUSIVE", "There are too few genuine reference images for this product.", None
        if reference_errors:
            return (
                "INCONCLUSIVE",
                "One or more genuine reference images could not be verified or loaded.",
                None,
            )
        if not self.config.calibrated:
            return (
                "INCONCLUSIVE",
                "Detection thresholds have not been calibrated against labeled genuine and counterfeit validation images.",
                None,
            )
        if packaging["status"] != "COMPARABLE" or clip_score is None:
            return "INCONCLUSIVE", "No reliable aligned packaging comparison was available.", None

        structural = packaging["structuralSimilarity"]
        color = packaging["colorSimilarity"]
        visual_difference = structural <= self.config.maximum_suspicious_ssim
        color_difference = color <= self.config.maximum_suspicious_color_similarity
        logo_difference = (
            logo["status"] == "COMPARABLE"
            and logo["structuralSimilarity"] <= self.config.maximum_suspicious_ssim
        )
        text_difference = text_evidence["status"] == "DIFFERENCES_FOUND"
        barcode_mismatch = barcode_evidence["status"] == "MISMATCH"

        if barcode_mismatch and clip_score < self.config.minimum_clip_similarity:
            return (
                "INCONCLUSIVE",
                "Barcode and visual reference evidence conflict; the product match is uncertain.",
                None,
            )
        if (
            (barcode_mismatch and identified["identificationEvidence"] != "EXACT_BARCODE")
            or (
                text_difference
                and text_evidence["confidentRegions"]
                >= self.config.minimum_ocr_regions_for_detection
            )
            or (text_difference and visual_difference)
            or logo_difference
            or visual_difference
            or (color_difference and visual_difference)
        ):
            confidence = round(min(
                1.0,
                max(
                    1.0 - structural,
                    text_evidence.get("mismatchRatio") or 0.0,
                    1.0 - clip_score,
                ),
            ), 4)
            return (
                "SUSPICIOUS",
                "Independent barcode, OCR, or aligned visual evidence shows a discrepancy. This is a preliminary assessment, not an authenticity verdict.",
                confidence,
            )

        text_clear = text_evidence["status"] in {
            "NO_SIGNIFICANT_DIFFERENCE",
            "REFERENCE_TEXT_NOT_AVAILABLE",
            "OCR_NOT_CONFIDENT",
        }
        barcode_clear = barcode_evidence["status"] != "MISMATCH"
        if (
            clip_score >= self.config.minimum_clip_similarity
            and structural >= self.config.minimum_consistent_ssim
            and color >= self.config.minimum_consistent_color_similarity
            and text_clear
            and barcode_clear
            and not logo_difference
        ):
            confidence = round(min(
                clip_score,
                structural,
                identified["identificationConfidence"],
            ), 4)
            return (
                "LIKELY_GENUINE",
                "Available aligned visual evidence is consistent with the stored references and no significant discrepancy was detected. This is not a certificate of authenticity.",
                confidence,
            )

        return (
            "INCONCLUSIVE",
            "Evidence is mixed or does not meet the configured criteria for a preliminary outcome.",
            None,
        )
