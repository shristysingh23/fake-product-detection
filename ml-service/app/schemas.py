"""Pydantic models for the stable image-analysis API response."""

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
    """OCR output and catalog-based product identification result."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "brand": "",
                    "product": "",
                    "status": "NOT_FOUND",
                    "identification_source": "product_catalog",
                    "extracted_text": "",
                    "ocr_lines": [],
                }
            ]
        }
    )

    brand: str = Field(description="Identified canonical brand, or an empty string if unresolved.")
    product: str = Field(description="Identified canonical product, or an empty string if unresolved.")
    status: str = Field(description="One of IDENTIFIED, AMBIGUOUS, or NOT_FOUND.")
    identification_source: str = Field(
        default="product_catalog",
        description="Source of the identification result; product_catalog for catalog matching.",
    )
    extracted_text: str = Field(default="", description="all recognized lines joined by newlines")
    ocr_lines: List[OcrLineOut] = Field(default_factory=list)
