package com.fpd.backend.dto.request;

import java.time.LocalDate;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ProductVersionRequestDto(
		@NotBlank @Size(max = 200) @Schema(example = "2025 Packaging") String versionName,
		@NotBlank @Size(max = 100) @Schema(example = "2025-v1") String versionCode,
		LocalDate releaseDate,
		@Size(max = 5000) String description,
		@Size(max = 10000) String packagingDetails,
		@Schema(example = "true") Boolean active) {
}
