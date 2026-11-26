"""Structured response models for product image extraction."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class TextRegion(BaseModel):
    text: str
    confidence: float | None = None


class Barcode(BaseModel):
    type: str
    value: str


class QRCode(BaseModel):
    type: str = "QR_CODE"
    value: str


class VisualMatch(BaseModel):
    productId: int
    referenceImageId: int
    similarityScore: float = Field(ge=-1.0, le=1.0)


class IdentifiedProduct(BaseModel):
    productId: int
    brand: str | None = None
    productName: str | None = None
    identificationConfidence: float | None = Field(default=None, ge=0.0, le=1.0)
    identificationEvidence: str


class ComparisonResult(BaseModel):
    status: str
    structuralSimilarity: float | None = Field(default=None, ge=-1.0, le=1.0)
    colorSimilarity: float | None = Field(default=None, ge=0.0, le=1.0)
    bestReferenceImageId: int | None = None
    referencesCompared: list[dict] = Field(default_factory=list)


class OcrDiscrepancyResult(BaseModel):
    status: str
    mismatchRatio: float | None = Field(default=None, ge=0.0, le=1.0)
    missingExpectedTokens: list[str] = Field(default_factory=list)
    unexpectedObservedTokens: list[str] = Field(default_factory=list)
    confidentRegions: int = 0


class BarcodeEvidence(BaseModel):
    status: str
    observedValues: list[str] = Field(default_factory=list)
    expectedValue: str | None = None
    note: str


class ImageQualityResult(BaseModel):
    status: str
    width: int | None = None
    height: int | None = None
    blurScore: float | None = None
    issues: list[str] = Field(default_factory=list)


class SuspiciousObservation(BaseModel):
    type: str
    referenceImageId: int | None = None
    region: dict | None = None
    description: str | None = None


class VisualDetectionResult(BaseModel):
    outcome: Literal["LIKELY_GENUINE", "SUSPICIOUS", "INCONCLUSIVE"]
    overallConfidence: float | None = Field(default=None, ge=0.0, le=1.0)
    calibrationStatus: Literal["CALIBRATED", "NOT_CALIBRATED"]
    identifiedProduct: IdentifiedProduct | None = None
    clipSimilarityScore: float | None = Field(default=None, ge=-1.0, le=1.0)
    logoComparison: ComparisonResult
    packagingComparison: ComparisonResult
    ocrDiscrepancies: OcrDiscrepancyResult
    barcodeEvidence: BarcodeEvidence
    imageQuality: ImageQualityResult
    suspiciousObservations: list[SuspiciousObservation] = Field(default_factory=list)
    referenceIssues: list[str] = Field(default_factory=list)
    explanation: str


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "processingStatus": "COMPLETED",
                "extractedText": [{"text": "MAGGI", "confidence": 0.98}],
                "barcodes": [{"type": "EAN13", "value": "8901234567890"}],
                "qrCodes": [],
                "processingErrors": [],
                "brand": "MAGGI",
                "product": "2-Minute Noodles",
                "status": "IDENTIFIED",
                "candidates": [],
                "visualMatches": [
                    {
                        "productId": 12,
                        "referenceImageId": 5,
                        "similarityScore": 0.91,
                    }
                ],
                "visualDetection": {
                    "outcome": "INCONCLUSIVE",
                    "overallConfidence": None,
                    "calibrationStatus": "NOT_CALIBRATED",
                    "explanation": "Detection thresholds require calibration."
                }
            }]
        }
    )

    processingStatus: str = Field(description="COMPLETED or PARTIALLY_COMPLETED")
    extractedText: list[TextRegion] = Field(default_factory=list)
    barcodes: list[Barcode] = Field(default_factory=list)
    qrCodes: list[QRCode] = Field(default_factory=list)
    processingErrors: list[str] = Field(default_factory=list)
    preprocessing: dict | None = None

    # Legacy fields retained for Phase 1 and existing Spring DTO compatibility.
    brand: str | None = None
    product: str | None = None
    status: str = "NOT_IDENTIFIED"
    candidates: list[dict] = Field(default_factory=list)
    visualMatches: list[VisualMatch] = Field(default_factory=list)
    visualDetection: VisualDetectionResult
