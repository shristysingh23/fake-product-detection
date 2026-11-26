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
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import com.fpd.backend.dto.request.BrandCreateRequestDto;
import com.fpd.backend.dto.request.BrandUpdateRequestDto;
import com.fpd.backend.dto.response.BrandResponseDto;
import com.fpd.backend.service.BrandService;

import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/brands")
@Tag(name = "Brands")
public class BrandController {
	private final BrandService brandService;

	public BrandController(BrandService brandService) {
		this.brandService = brandService;
	}

	@PostMapping
	@Operation(summary = "Create a brand")
	@ApiResponses({
		@ApiResponse(responseCode = "201", description = "Brand created"),
		@ApiResponse(responseCode = "400", description = "Invalid brand input"),
		@ApiResponse(responseCode = "409", description = "Brand name already exists")
	})
	public ResponseEntity<BrandResponseDto> create(@Valid @RequestBody BrandCreateRequestDto request) {
		BrandResponseDto response = brandService.create(request);
		URI location = ServletUriComponentsBuilder.fromCurrentRequest()
				.path("/{id}").buildAndExpand(response.id()).toUri();
		return ResponseEntity.created(location).body(response);
	}

	@GetMapping
	@Operation(summary = "List brands")
	public List<BrandResponseDto> findAll() {
		return brandService.findAll();
	}

	@GetMapping("/{id}")
	@Operation(summary = "Get a brand by ID")
	@ApiResponse(responseCode = "404", description = "Brand not found")
	public BrandResponseDto findById(@PathVariable Long id) {
		return brandService.findById(id);
	}

	@PutMapping("/{id}")
	@Operation(summary = "Update a brand")
	@ApiResponses({
		@ApiResponse(responseCode = "400", description = "Invalid brand input"),
		@ApiResponse(responseCode = "404", description = "Brand not found"),
		@ApiResponse(responseCode = "409", description = "Brand name already exists")
	})
	public BrandResponseDto update(@PathVariable Long id,
			@Valid @RequestBody BrandUpdateRequestDto request) {
		return brandService.update(id, request);
	}

	@DeleteMapping("/{id}")
	@Operation(summary = "Delete a brand")
	@ApiResponses({
		@ApiResponse(responseCode = "204", description = "Brand deleted"),
		@ApiResponse(responseCode = "404", description = "Brand not found"),
		@ApiResponse(responseCode = "409", description = "Brand has dependent products")
	})
	public ResponseEntity<Void> delete(@PathVariable Long id) {
		brandService.delete(id);
		return ResponseEntity.noContent().build();
	}
}
