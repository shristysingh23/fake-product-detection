package com.fpd.backend.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import io.swagger.v3.oas.annotations.media.Schema;

public record BrandCreateRequestDto(
		@NotBlank @Size(max = 200) @Schema(example = "Adidas") String name,
		@Size(max = 5000) String description,
		@Size(max = 500) @Schema(example = "https://www.adidas.com") String officialWebsite,
		@Size(max = 100) @Schema(example = "Germany") String country) {
}
