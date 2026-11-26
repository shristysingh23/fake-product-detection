package com.fpd.backend.dto.response;

import java.time.Instant;

public record BrandResponseDto(
		Long id, String name, String description, String officialWebsite,
		String country, Instant createdAt, Instant updatedAt) {
}
