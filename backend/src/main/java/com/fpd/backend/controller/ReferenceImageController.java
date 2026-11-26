package com.fpd.backend.controller;

import java.net.URI;
import java.util.List;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import com.fpd.backend.dto.response.ReferenceImageResponseDto;
import com.fpd.backend.dto.response.VisualReferenceImageDto;
import com.fpd.backend.entity.ProductReferenceImage.ImageType;
import com.fpd.backend.service.ReferenceImageService;

import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.Parameter;

@RestController
@Tag(name = "Product Reference Images")
public class ReferenceImageController {
	private final ReferenceImageService imageService;

	public ReferenceImageController(ReferenceImageService imageService) {
		this.imageService = imageService;
	}

	@PostMapping(value = "/api/versions/{versionId}/images",
			consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
	@Operation(summary = "Upload a genuine product reference image",
			description = "Accepts JPEG, PNG, or WebP, up to the configured size limit.")
	@ApiResponses({
		@ApiResponse(responseCode = "201", description = "Image stored locally and metadata created"),
		@ApiResponse(responseCode = "400", description = "Missing, unsupported, empty, or invalid image"),
		@ApiResponse(responseCode = "404", description = "Product version not found")
	})
	public ResponseEntity<ReferenceImageResponseDto> upload(
			@PathVariable Long versionId,
			@Parameter(description = "JPEG, PNG, or WebP reference image")
			@RequestParam("image") MultipartFile image,
			@Parameter(description = "Reference view or region")
			@RequestParam("imageType") ImageType imageType,
			@RequestParam(name = "viewType", required = false) String viewType) {
		ReferenceImageResponseDto response =
				imageService.upload(versionId, image, imageType, viewType);
		URI location = ServletUriComponentsBuilder.fromCurrentRequest()
				.path("/{imageId}").buildAndExpand(response.id()).toUri();
		return ResponseEntity.created(location).body(response);
	}

	@GetMapping("/api/versions/{versionId}/images")
	@Operation(summary = "List reference image metadata for a version")
	public List<ReferenceImageResponseDto> findByVersion(@PathVariable Long versionId) {
		return imageService.findByVersion(versionId);
	}

	@GetMapping("/api/images/{imageId}")
	@Operation(summary = "Get reference image metadata")
	@ApiResponse(responseCode = "404", description = "Reference image not found")
	public ReferenceImageResponseDto findById(@PathVariable Long imageId) {
		return imageService.findById(imageId);
	}

	@PutMapping(value = "/api/images/{imageId}/content",
			consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
	@Operation(summary = "Replace a genuine product reference image",
			description = "The ML service detects the changed file timestamp and regenerates its cached embedding.")
	@ApiResponses({
		@ApiResponse(responseCode = "200", description = "Reference image replaced"),
		@ApiResponse(responseCode = "400", description = "Missing, unsupported, empty, or invalid image"),
		@ApiResponse(responseCode = "404", description = "Reference image not found")
	})
	public ReferenceImageResponseDto updateContent(
			@PathVariable Long imageId,
			@RequestParam("image") MultipartFile image) {
		return imageService.updateContent(imageId, image);
	}

	@GetMapping("/api/ml/reference-images")
	@Operation(summary = "List genuine reference images for visual matching",
			description = "Returns image metadata and version information; image bytes are fetched separately.")
	public List<VisualReferenceImageDto> findVisualReferences() {
		return imageService.findVisualReferences();
	}

	@GetMapping("/api/ml/reference-images/{imageId}/content")
	@Operation(summary = "Read a genuine reference image for visual matching")
	@ApiResponses({
		@ApiResponse(responseCode = "200", description = "Reference image content"),
		@ApiResponse(responseCode = "404", description = "Reference image or stored content not found")
	})
	public ResponseEntity<byte[]> readVisualReference(@PathVariable Long imageId) {
		ReferenceImageResponseDto metadata = imageService.findById(imageId);
		byte[] content = imageService.readContent(imageId);
		return ResponseEntity.ok()
				.contentType(MediaType.parseMediaType(metadata.contentType()))
				.header(HttpHeaders.CONTENT_LENGTH, Integer.toString(content.length))
				.body(content);
	}

	@DeleteMapping("/api/images/{imageId}")
	@Operation(summary = "Delete a reference image and its local file")
	@ApiResponses({
		@ApiResponse(responseCode = "204", description = "Image deleted"),
		@ApiResponse(responseCode = "404", description = "Reference image not found")
	})
	public ResponseEntity<Void> delete(@PathVariable Long imageId) {
		imageService.delete(imageId);
		return ResponseEntity.noContent().build();
	}
}
