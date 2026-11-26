package com.fpd.backend.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import com.fpd.backend.entity.ProductReferenceImage.ImageType;

public record ReferenceImageUploadDto(
		@NotNull ImageType imageType,
		@Size(max = 100) String viewType) {
}
