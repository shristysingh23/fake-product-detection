package com.fpd.backend.dto.response;

public record ProductResponseDto(
		Long id,
		String brand,
		String productName,
		String category,
		String barcode,
		String expectedText) {
}
