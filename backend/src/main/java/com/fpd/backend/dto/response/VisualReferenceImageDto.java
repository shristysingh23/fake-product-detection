package com.fpd.backend.dto.response;

public record VisualReferenceImageDto(
		Long referenceImageId,
		Long productId,
		String brand,
		String productName,
		String expectedText,
		String barcode,
		String imageType,
		String contentType,
		long fileSize,
		long lastModifiedNanos,
		boolean available) {
}
