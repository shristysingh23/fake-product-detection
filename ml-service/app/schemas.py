"""Pydantic models for the dummy analysis response used until Days 7-13."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class OcrLineOut(BaseModel):
    text: str = Field(description="Recognized text of one line.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="OCR confidence from 0 to 1. A model score, not proof that the text is correct.",
    )


class AnalyzeResponse(BaseModel):
    """Fixed dummy response while image analysis is not implemented."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "brand": "MAGGI",
                    "product": "2-Minute Noodles",
                    "status": "ANALYSIS_PENDING",
                    "identification_source": "placeholder",
                    "extracted_text": "Maggi\n2-Minute",
                    "ocr_lines": [
                        {"text": "Maggi", "confidence": 1.0},
                        {"text": "2-Minute", "confidence": 0.8},
                    ],
                }
            ]
        }
    )

    # These values are placeholders until real analysis is added.
    brand: str = Field(description="Dummy brand label for the pending analysis.")
    product: str = Field(description="Dummy product name for the pending analysis.")
    status: str = Field(description="Current processing status of the analysis.")
    identification_source: str = Field(
        default="placeholder",
        description="brand and product are still fixed demo values, not derived from the image",
    )
    extracted_text: str = Field(default="", description="all recognized lines joined by newlines")
    ocr_lines: List[OcrLineOut] = Field(default_factory=list)
