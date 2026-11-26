package com.fpd.backend.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import io.swagger.v3.oas.annotations.media.Schema;

public record ProductUpdateRequestDto(
		@NotBlank
		@Size(max = 120)
		@Schema(example = "New Acme")
		String brand,
		@NotBlank
		@Size(max = 200)
		@Schema(example = "New Cereal")
		String productName,
		@NotBlank
		@Size(max = 100)
		@Schema(example = "Breakfast")
		String category,
		@Size(max = 64)
		@Schema(example = "0098765432105")
		String barcode,
		@Size(max = 5000)
		@Schema(example = "Updated package text")
		String expectedText,
		@Schema(example = "1")
		Long brandId) {

	public ProductUpdateRequestDto(String brand, String productName, String category,
			String barcode, String expectedText) {
		this(brand, productName, category, barcode, expectedText, null);
	}
}
