package com.fpd.backend.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

public record ProductCandidateDto(
		@Schema(example = "42") Long productId,
		@Schema(example = "Acme") String brand,
		@Schema(example = "Cereal") String productName,
		@Schema(example = "8901234567890") String matchingBarcode,
		@Schema(example = "Exact barcode match") String matchingEvidence,
		@Schema(example = "1.0",
				description = "Product identification score only; it is not an authenticity probability")
		double matchConfidence,
		@Schema(example = "IDENTIFIED") String identificationStatus) {
}
