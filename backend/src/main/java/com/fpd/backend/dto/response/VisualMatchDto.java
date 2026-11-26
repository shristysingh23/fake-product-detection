package com.fpd.backend.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

public record VisualMatchDto(
		@Schema(example = "12") Long productId,
		@Schema(example = "5") Long referenceImageId,
		@Schema(example = "0.91", description = "CLIP cosine similarity; not an authenticity probability")
		double similarityScore) {
}
