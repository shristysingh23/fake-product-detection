package com.fpd.backend.dto.response;

import java.util.List;
import java.util.Map;

import io.swagger.v3.oas.annotations.media.Schema;

public record AnalyzeResponseDto(
		@Schema(example = "MAGGI") String brand,
		@Schema(example = "2-Minute Noodles") String product,
		@Schema(example = "NOT_IDENTIFIED") String status,
		@Schema(example = "COMPLETED") String processingStatus,
		List<TextRegionDto> extractedText,
		List<BarcodeDto> barcodes,
		List<BarcodeDto> qrCodes,
		List<String> processingErrors,
		List<ProductCandidateDto> candidates,
		Object preprocessing,
		List<VisualMatchDto> visualMatches,
		@Schema(description = "Preliminary explainable visual assessment; not an authenticity certificate",
				example = "{\"outcome\":\"INCONCLUSIVE\",\"calibrationStatus\":\"NOT_CALIBRATED\"}")
		Map<String, Object> visualDetection) {

	public AnalyzeResponseDto(String brand, String product, String status) {
		this(brand, product, status, "COMPLETED", List.of(), List.of(), List.of(),
				List.of(), List.of(), null, List.of(), null);
	}

	public AnalyzeResponseDto(String brand, String product, String status,
			String processingStatus, List<TextRegionDto> extractedText,
			List<BarcodeDto> barcodes, List<BarcodeDto> qrCodes,
			List<String> processingErrors, List<ProductCandidateDto> candidates,
			Object preprocessing, List<VisualMatchDto> visualMatches) {
		this(brand, product, status, processingStatus, extractedText, barcodes,
				qrCodes, processingErrors, candidates, preprocessing, visualMatches, null);
	}

	public AnalyzeResponseDto(String brand, String product, String status,
			String processingStatus, List<TextRegionDto> extractedText,
			List<BarcodeDto> barcodes, List<BarcodeDto> qrCodes,
			List<String> processingErrors, List<ProductCandidateDto> candidates,
			Object preprocessing) {
		this(brand, product, status, processingStatus, extractedText, barcodes,
				qrCodes, processingErrors, candidates, preprocessing, List.of(), null);
	}

	public record TextRegionDto(
			@Schema(example = "MAGGI") String text,
			@Schema(example = "0.98") Double confidence) {
	}

	public record BarcodeDto(
			@Schema(example = "EAN13") String type,
			@Schema(example = "8901234567890") String value) {
	}
}
