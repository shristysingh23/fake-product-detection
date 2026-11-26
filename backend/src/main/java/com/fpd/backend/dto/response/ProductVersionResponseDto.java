package com.fpd.backend.dto.response;

import java.time.Instant;
import java.time.LocalDate;

public record ProductVersionResponseDto(
		Long id, Long productId, String versionName, String versionCode,
		LocalDate releaseDate, String description, String packagingDetails,
		boolean active, Instant createdAt, Instant updatedAt) {
}
