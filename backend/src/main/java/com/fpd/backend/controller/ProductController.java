package com.fpd.backend.controller;

import java.net.URI;
import java.util.Locale;
import java.util.Set;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import com.fpd.backend.dto.request.ProductCreateRequestDto;
import com.fpd.backend.dto.request.ProductUpdateRequestDto;
import com.fpd.backend.dto.response.ApiErrorResponse;
import com.fpd.backend.dto.response.ProductResponseDto;
import com.fpd.backend.service.ProductService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductController {

	private static final int MAX_PAGE_SIZE = 100;
	private static final Set<String> ALLOWED_SORT_FIELDS = Set.of(
			"id", "brand", "productName", "category", "barcode", "expectedText");

	private final ProductService productService;

	@PostMapping
	public ResponseEntity<ProductResponseDto> createProduct(
			@Valid @RequestBody ProductCreateRequestDto request) {
		ProductResponseDto response = productService.createProduct(request);
		URI location = ServletUriComponentsBuilder.fromCurrentRequest()
				.path("/{id}")
				.buildAndExpand(response.id())
				.toUri();

		return ResponseEntity.created(location).body(response);
	}

	@GetMapping
	public ResponseEntity<?> getAllProducts(
			@RequestParam(name = "page", defaultValue = "0") int page,
			@RequestParam(name = "size", defaultValue = "10") int size,
			@RequestParam(name = "sortBy", defaultValue = "id") String sortBy,
			@RequestParam(name = "direction", defaultValue = "ASC") String direction) {
		if (page < 0) {
			return badRequest("Page number must be zero or greater.");
		}
		if (size < 1) {
			return badRequest("Page size must be at least 1.");
		}
		if (size > MAX_PAGE_SIZE) {
			return badRequest("Page size must not exceed " + MAX_PAGE_SIZE + ".");
		}
		if (!ALLOWED_SORT_FIELDS.contains(sortBy)) {
			return badRequest("Unsupported sort field.");
		}
		if (!"ASC".equalsIgnoreCase(direction) && !"DESC".equalsIgnoreCase(direction)) {
			return badRequest("Direction must be ASC or DESC.");
		}

		Sort.Direction sortDirection = Sort.Direction.valueOf(direction.toUpperCase(Locale.ROOT));
		Pageable pageable = PageRequest.of(page, size, Sort.by(sortDirection, sortBy));

		return ResponseEntity.ok(productService.getAllProducts(pageable));
	}

	@GetMapping("/{id}")
	public ResponseEntity<ProductResponseDto> getProductById(@PathVariable Long id) {
		return ResponseEntity.ok(productService.getProductById(id));
	}

	@PutMapping("/{id}")
	public ResponseEntity<ProductResponseDto> updateProduct(
			@PathVariable Long id,
			@Valid @RequestBody ProductUpdateRequestDto request) {
		return ResponseEntity.ok(productService.updateProduct(id, request));
	}

	@DeleteMapping("/{id}")
	public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
		productService.deleteProduct(id);
		return ResponseEntity.noContent().build();
	}

	private ResponseEntity<ApiErrorResponse> badRequest(String message) {
		return ResponseEntity.badRequest()
				.body(ApiErrorResponse.from(HttpStatus.BAD_REQUEST, message));
	}
}
