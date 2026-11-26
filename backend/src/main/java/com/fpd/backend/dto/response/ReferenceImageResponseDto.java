package com.fpd.backend.dto.response;

import java.time.Instant;

import com.fpd.backend.entity.ProductReferenceImage.ImageType;

public record ReferenceImageResponseDto(
		Long id, Long productVersionId, String imageUrl, String storageKey,
		ImageType imageType, String viewType, String originalFilename,
		String contentType, long fileSize, Instant createdAt) {
}
