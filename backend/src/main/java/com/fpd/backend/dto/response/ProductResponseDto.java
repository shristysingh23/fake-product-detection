package com.fpd.backend.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

public record ProductResponseDto(
		@Schema(example = "42") Long id,
		@Schema(example = "Acme") String brand,
		@Schema(example = "Cereal") String productName,
		@Schema(example = "Food") String category,
		@Schema(example = "0012345678905") String barcode,
		@Schema(example = "Genuine package text") String expectedText,
		@Schema(example = "1") Long brandId) {

	public ProductResponseDto(Long id, String brand, String productName, String category,
			String barcode, String expectedText) {
		this(id, brand, productName, category, barcode, expectedText, null);
	}
}
