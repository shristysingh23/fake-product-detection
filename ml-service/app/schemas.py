"""Pydantic request and response models for the analysis endpoint."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyzeRequest(BaseModel):
    """Product details accepted by the dummy analysis endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"product_name": "AirPods Pro", "brand": "Apple", "price": 24999}
            ]
        }
    )

    # The product's name must contain a non-whitespace character.
    product_name: str = Field(
        min_length=1,
        description="Name of the product being checked.",
    )
    # The brand must contain a non-whitespace character.
    brand: str = Field(
        min_length=1,
        description="Brand printed on or associated with the product.",
    )
    # The listed price must be a number greater than zero.
    price: float = Field(
        gt=0,
        description="Listed product price; it must be greater than zero.",
    )

    @field_validator("product_name", "brand", mode="before")
    @classmethod
    def strip_text_fields(cls, value):
        """Remove surrounding spaces before checking required text fields."""
        if isinstance(value, str):
            return value.strip()
        return value


class AnalyzeResponse(BaseModel):
    """Fixed dummy result returned while real analysis is not implemented."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "product_name": "AirPods Pro",
                    "brand": "Apple",
                    "price": 24999,
                    "verdict": "SUSPICIOUS",
                    "confidence": 0.5,
                    "reasons": [
                        "Dummy response: real analysis is not implemented yet"
                    ],
                    "analysis_mode": "dummy",
                }
            ]
        }
    )

    # These fields echo the validated product information from the request.
    product_name: str = Field(description="Product name received in the request.")
    brand: str = Field(description="Brand received in the request.")
    price: float = Field(description="Price received in the request.")
    # Verdict is a string placeholder for future analysis results.
    verdict: str = Field(description="Dummy verdict; future values may vary.")
    # Confidence is a number from zero to one.
    confidence: float = Field(ge=0, le=1, description="Confidence from 0 to 1.")
    # Reasons explains the returned verdict in one or more text messages.
    reasons: list[str] = Field(description="Text explanations for the verdict.")
    # Analysis mode identifies this result as a dummy response.
    analysis_mode: str = Field(description="Processing mode used for this result.")
