"""Pydantic models for the dummy analysis response used until Days 7-13."""

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeResponse(BaseModel):
    """Fixed dummy response while image analysis is not implemented."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "brand": "MAGGI",
                    "product": "2-Minute Noodles",
                    "status": "ANALYSIS_PENDING",
                }
            ]
        }
    )

    # These values are placeholders until real analysis is added.
    brand: str = Field(description="Dummy brand label for the pending analysis.")
    product: str = Field(description="Dummy product name for the pending analysis.")
    status: str = Field(description="Current processing status of the analysis.")
