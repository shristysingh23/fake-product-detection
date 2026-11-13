package com.fpd.backend.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ProductCreateRequestDto(
		@NotBlank
		@Size(max = 120)
		String brand,
		@NotBlank
		@Size(max = 200)
		String productName,
		@NotBlank
		@Size(max = 100)
		String category,
		@Size(max = 64)
		String barcode,
		@Size(max = 5000)
		String expectedText) {
}
