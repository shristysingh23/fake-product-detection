package com.fpd.backend.controller;

import java.net.URI;
import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import com.fpd.backend.dto.request.ProductVersionRequestDto;
import com.fpd.backend.dto.response.ProductVersionResponseDto;
import com.fpd.backend.service.ProductVersionService;

import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;

@RestController
@Tag(name = "Product Versions")
public class ProductVersionController {
	private final ProductVersionService versionService;

	public ProductVersionController(ProductVersionService versionService) {
		this.versionService = versionService;
	}

	@PostMapping("/api/products/{productId}/versions")
	@Operation(summary = "Add a packaging version to a product")
	@ApiResponses({
		@ApiResponse(responseCode = "201", description = "Version created"),
		@ApiResponse(responseCode = "404", description = "Product not found"),
		@ApiResponse(responseCode = "409", description = "Version code already exists")
	})
	public ResponseEntity<ProductVersionResponseDto> create(
			@PathVariable Long productId,
			@Valid @RequestBody ProductVersionRequestDto request) {
		ProductVersionResponseDto response = versionService.create(productId, request);
		URI location = ServletUriComponentsBuilder.fromCurrentRequest()
				.path("/{id}").buildAndExpand(response.id()).toUri();
		return ResponseEntity.created(location).body(response);
	}

	@GetMapping("/api/products/{productId}/versions")
	@Operation(summary = "List versions for a product")
	public List<ProductVersionResponseDto> findByProduct(@PathVariable Long productId) {
		return versionService.findByProduct(productId);
	}

	@GetMapping("/api/versions/{versionId}")
	@Operation(summary = "Get a product version")
	@ApiResponse(responseCode = "404", description = "Version not found")
	public ProductVersionResponseDto findById(@PathVariable Long versionId) {
		return versionService.findById(versionId);
	}

	@PutMapping("/api/versions/{versionId}")
	@Operation(summary = "Update a product version")
	@ApiResponses({
		@ApiResponse(responseCode = "404", description = "Version not found"),
		@ApiResponse(responseCode = "409", description = "Version code already exists")
	})
	public ProductVersionResponseDto update(@PathVariable Long versionId,
			@Valid @RequestBody ProductVersionRequestDto request) {
		return versionService.update(versionId, request);
	}

	@DeleteMapping("/api/versions/{versionId}")
	@Operation(summary = "Delete a product version")
	@ApiResponses({
		@ApiResponse(responseCode = "204", description = "Version deleted"),
		@ApiResponse(responseCode = "404", description = "Version not found"),
		@ApiResponse(responseCode = "409", description = "Version has dependent reference images")
	})
	public ResponseEntity<Void> delete(@PathVariable Long versionId) {
		versionService.delete(versionId);
		return ResponseEntity.noContent().build();
	}
}
