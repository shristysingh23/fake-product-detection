package com.fpd.backend.controller;

import java.io.IOException;

import org.springframework.http.MediaType;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.fpd.backend.client.MlServiceClient;
import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.dto.response.MlHealthResponseDto;
import com.fpd.backend.service.ImageUploadValidator;
import com.fpd.backend.service.ProductIdentificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

@RestController
@RequestMapping("/api/ml")
@Tag(name = "ML Analysis", description = "Product image analysis integration")
public class MlController {

	private final MlServiceClient mlServiceClient;
	private final ImageUploadValidator imageUploadValidator;
	private final ProductIdentificationService productIdentificationService;

	public MlController(MlServiceClient mlServiceClient, ImageUploadValidator imageUploadValidator) {
		this(mlServiceClient, imageUploadValidator, null);
	}

	@Autowired
	public MlController(MlServiceClient mlServiceClient, ImageUploadValidator imageUploadValidator,
			ProductIdentificationService productIdentificationService) {
		this.mlServiceClient = mlServiceClient;
		this.imageUploadValidator = imageUploadValidator;
		this.productIdentificationService = productIdentificationService;
	}

	@PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
	@Operation(summary = "Analyze a product image",
			description = "Returns OCR/barcode identification, ranked CLIP matches, and a preliminary evidence-based visual assessment. Outcomes are INCONCLUSIVE until locally calibrated; no result is an authenticity certificate.")
	@RequestBody(required = true, content = @Content(mediaType = MediaType.MULTIPART_FORM_DATA_VALUE))
	@ApiResponses({
		@ApiResponse(responseCode = "200", description = "ML analysis response",
			content = @Content(schema = @Schema(implementation = AnalyzeResponseDto.class))),
		@ApiResponse(responseCode = "400", description = "Missing, malformed or invalid image"),
		@ApiResponse(responseCode = "502", description = "Unexpected ML service response"),
		@ApiResponse(responseCode = "503", description = "ML service unavailable"),
		@ApiResponse(responseCode = "504", description = "ML service timeout")
	})
	public AnalyzeResponseDto analyze(@RequestPart("image") MultipartFile image) throws IOException {
		imageUploadValidator.validate(image);
		AnalyzeResponseDto extraction = mlServiceClient.analyze(
				image.getBytes(), image.getOriginalFilename(), image.getContentType());
		return productIdentificationService == null
				? extraction
				: productIdentificationService.identify(extraction);
	}

	@GetMapping("/health")
	@Operation(summary = "Check ML service health")
	@ApiResponses({
		@ApiResponse(responseCode = "200", description = "ML service is healthy"),
		@ApiResponse(responseCode = "502", description = "Unexpected ML health response"),
		@ApiResponse(responseCode = "503", description = "ML service unavailable"),
		@ApiResponse(responseCode = "504", description = "ML service timeout")
	})
	public MlHealthResponseDto health() {
		return mlServiceClient.health();
	}
}
