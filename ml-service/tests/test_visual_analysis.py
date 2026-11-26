import numpy as np
import cv2
import pytest
from PIL import Image

from app.visual_analysis import (
    VisualDetectionConfig,
    VisualDetectionEngine,
    compare_aligned_images,
)
from app.visual_matching import CachedReference


def make_reference(reference_id, image_type="FRONT", barcode=None, mark=10):
    if image_type == "LOGO" and mark == 10:
        mark = 250
    image = Image.new("RGB", (200, 200), color=(mark, 60, 90))
    return reference_id, CachedReference(
        product_id=12,
        fingerprint=(1, 1, "image/png"),
        embedding=np.array([1.0, 0.0], dtype=np.float32),
        image=image,
        brand="Acme",
        product_name="Widget Premium",
        expected_text="Acme Widget Premium",
        barcode=barcode,
        image_type=image_type,
    )


def make_engine(config=None, structural=0.95, color=0.95, logo_structural=0.95):
    def comparator(image_bgr, reference, _config):
        logo = reference.getpixel((0, 0))[0] == 250
        score = logo_structural if logo else structural
        return {
            "status": "COMPARABLE",
            "structuralSimilarity": score,
            "colorSimilarity": color,
            "suspiciousRegions": [],
        }

    return VisualDetectionEngine(
        config or VisualDetectionConfig(calibrated=True),
        comparator=comparator,
    )


def analyze(engine, references=None, text=None, barcodes=None, matches=None, quality=None):
    if references is None:
        references = [
            make_reference(1),
            make_reference(2, mark=20),
            make_reference(3, image_type="LOGO"),
        ]
    if matches is None:
        matches = [
            {"productId": 12, "referenceImageId": reference_id, "similarityScore": 0.94}
            for reference_id, _ in references
        ]
    if text is None:
        text = [
            {"text": token, "confidence": 0.98}
            for token in ("Acme", "Widget", "Premium")
        ]
    return engine.analyze(
        np.zeros((200, 200, 3), dtype=np.uint8),
        references,
        matches,
        text,
        barcodes or [],
        [],
        quality or {
            "originalDimensions": {"width": 200, "height": 200},
            "blurScore": 100.0,
        },
    )


def test_genuine_like_references_return_likely_genuine_when_calibrated():
    result = analyze(make_engine())

    assert result["outcome"] == "LIKELY_GENUINE"
    assert result["identifiedProduct"]["productId"] == 12
    assert result["packagingComparison"]["structuralSimilarity"] == 0.95
    assert result["overallConfidence"] is not None


def test_logo_difference_is_reported_as_suspicious():
    result = analyze(make_engine(logo_structural=0.2))

    assert result["outcome"] == "SUSPICIOUS"
    assert result["logoComparison"]["structuralSimilarity"] == 0.2


def test_packaging_difference_is_reported_as_suspicious():
    result = analyze(make_engine(structural=0.3))

    assert result["outcome"] == "SUSPICIOUS"
    assert result["packagingComparison"]["structuralSimilarity"] == 0.3


def test_multiple_confident_ocr_regions_can_flag_text_mismatch():
    result = analyze(
        make_engine(),
        text=[
            {"text": "Acme", "confidence": 0.98},
            {"text": "Widget", "confidence": 0.98},
            {"text": "Replacement", "confidence": 0.98},
        ],
    )

    assert result["outcome"] == "SUSPICIOUS"
    assert result["ocrDiscrepancies"]["status"] == "DIFFERENCES_FOUND"
    assert "premium" in result["ocrDiscrepancies"]["missingExpectedTokens"]


def test_barcode_conflict_does_not_override_exact_barcode_identification():
    references = [
        make_reference(1, barcode="1111"),
        make_reference(2, barcode="1111", mark=20),
        make_reference(3, image_type="LOGO", barcode="1111"),
        (4, CachedReference(
            product_id=13,
            fingerprint=(1, 1, "image/png"),
            embedding=np.array([0.0, 1.0], dtype=np.float32),
            image=Image.new("RGB", (200, 200), color=(30, 60, 90)),
            brand="Other",
            product_name="Product",
            expected_text="Other Product",
            barcode="9999",
            image_type="FRONT",
        )),
    ]
    matches = [
        {"productId": 12, "referenceImageId": 1, "similarityScore": 0.4},
        {"productId": 13, "referenceImageId": 4, "similarityScore": 0.99},
    ]
    result = analyze(
        make_engine(),
        references=references,
        matches=matches,
        barcodes=[{"type": "EAN13", "value": "1111"}],
    )

    assert result["identifiedProduct"]["productId"] == 12
    assert result["identifiedProduct"]["identificationEvidence"] == "EXACT_BARCODE"
    assert result["outcome"] == "INCONCLUSIVE"
    assert result["barcodeEvidence"]["status"] == "MATCH"


def test_unexpected_barcode_is_reported_as_suspicious_evidence():
    references = [
        make_reference(1, barcode="1111"),
        make_reference(2, barcode="1111", mark=20),
        make_reference(3, image_type="LOGO", barcode="1111"),
    ]
    result = analyze(
        make_engine(),
        references=references,
        barcodes=[{"type": "EAN13", "value": "2222"}],
    )

    assert result["outcome"] == "SUSPICIOUS"
    assert result["barcodeEvidence"]["status"] == "MISMATCH"


def test_low_quality_image_is_inconclusive():
    result = analyze(
        make_engine(),
        quality={
            "originalDimensions": {"width": 80, "height": 80},
            "blurScore": 2.0,
        },
    )

    assert result["outcome"] == "INCONCLUSIVE"
    assert result["imageQuality"]["status"] == "LOW"


def test_missing_references_are_inconclusive_without_fabricated_scores():
    result = analyze(make_engine(), references=[], matches=[])

    assert result["outcome"] == "INCONCLUSIVE"
    assert result["identifiedProduct"] is None
    assert result["clipSimilarityScore"] is None
    assert result["packagingComparison"]["structuralSimilarity"] is None


def test_uncalibrated_thresholds_never_claim_genuine_or_suspicious():
    result = analyze(make_engine(VisualDetectionConfig(calibrated=False)))

    assert result["outcome"] == "INCONCLUSIVE"
    assert result["overallConfidence"] is None
    assert result["calibrationStatus"] == "NOT_CALIBRATED"


def test_unavailable_analysis_has_no_comparison_scores():
    result = make_engine().unavailable("comparison unavailable")

    assert result["outcome"] == "INCONCLUSIVE"
    assert result["clipSimilarityScore"] is None
    assert result["logoComparison"]["structuralSimilarity"] is None


def test_invalid_calibration_threshold_relationship_is_rejected():
    with pytest.raises(ValueError, match="Suspicious SSIM threshold"):
        VisualDetectionConfig(
            minimum_consistent_ssim=0.4,
            maximum_suspicious_ssim=0.5,
        )


def test_alignment_tolerates_small_rotation_and_lighting_change():
    reference_bgr = np.full((400, 400, 3), 245, dtype=np.uint8)
    cv2.rectangle(reference_bgr, (90, 50), (310, 350), (40, 120, 190), -1)
    cv2.rectangle(reference_bgr, (110, 80), (290, 320), (245, 245, 245), 3)
    for index in range(6):
        cv2.line(
            reference_bgr,
            (120, 110 + index * 30),
            (280, 110 + index * 30),
            (30, 30, 30),
            2,
        )
    cv2.putText(
        reference_bgr,
        "ACME",
        (130, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (20, 20, 20),
        2,
    )
    rotation = cv2.getRotationMatrix2D((200, 200), 6, 1.0)
    uploaded_bgr = cv2.warpAffine(
        reference_bgr, rotation, (400, 400), borderValue=(230, 230, 230)
    )
    uploaded_bgr = np.clip(
        uploaded_bgr.astype(np.int16) + 12, 0, 255
    ).astype(np.uint8)

    comparison = compare_aligned_images(
        uploaded_bgr,
        Image.fromarray(cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2RGB)),
        VisualDetectionConfig(),
    )

    assert comparison["status"] == "COMPARABLE"
    assert comparison["alignmentInliers"] >= 8
    assert comparison["structuralSimilarity"] > 0.78
    assert comparison["colorSimilarity"] > 0.72
