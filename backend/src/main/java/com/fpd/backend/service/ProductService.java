package com.fpd.backend.service;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import com.fpd.backend.dto.request.ProductCreateRequestDto;
import com.fpd.backend.dto.request.ProductUpdateRequestDto;
import com.fpd.backend.dto.response.ProductResponseDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.exception.ProductNotFoundException;
import com.fpd.backend.repository.ProductRepository;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class ProductService {

	private static final int MAX_PAGE_SIZE = 100;

	private final ProductRepository productRepository;

	public ProductResponseDto createProduct(ProductCreateRequestDto request) {
		Product product = new Product(
				request.brand(),
				request.productName(),
				request.category(),
				request.barcode(),
				request.expectedText());

		return mapToResponseDto(productRepository.save(product));
	}

	public ProductResponseDto getProductById(Long id) {
		Product product = productRepository.findById(id)
				.orElseThrow(() -> new ProductNotFoundException("Product with id " + id + " was not found."));

		return mapToResponseDto(product);
	}

	public List<ProductResponseDto> getAllProducts() {
		return productRepository.findAll()
				.stream()
				.map(this::mapToResponseDto)
				.toList();
	}

	public Page<ProductResponseDto> getAllProducts(Pageable pageable) {
		validatePageable(pageable);

		Pageable effectivePageable = pageable.getSort().isSorted()
				? pageable
				: PageRequest.of(pageable.getPageNumber(), pageable.getPageSize(),
						Sort.by(Sort.Direction.ASC, "id"));

		return productRepository.findAll(effectivePageable)
				.map(this::mapToResponseDto);
	}

	public ProductResponseDto updateProduct(Long id, ProductUpdateRequestDto request) {
		Product product = productRepository.findById(id)
				.orElseThrow(() -> new ProductNotFoundException("Product with id " + id + " was not found."));

		product.setBrand(request.brand());
		product.setProductName(request.productName());
		product.setCategory(request.category());
		product.setBarcode(request.barcode());
		product.setExpectedText(request.expectedText());

		return mapToResponseDto(productRepository.save(product));
	}

	public void deleteProduct(Long id) {
		Product product = productRepository.findById(id)
				.orElseThrow(() -> new ProductNotFoundException("Product with id " + id + " was not found."));

		productRepository.delete(product);
	}

	private ProductResponseDto mapToResponseDto(Product product) {
		return new ProductResponseDto(
				product.getId(),
				product.getBrand(),
				product.getProductName(),
				product.getCategory(),
				product.getBarcode(),
				product.getExpectedText());
	}

	private void validatePageable(Pageable pageable) {
		if (pageable.isUnpaged()) {
			throw new IllegalArgumentException("A paged request is required.");
		}
		if (pageable.getPageNumber() < 0) {
			throw new IllegalArgumentException("Page number must be zero or greater.");
		}
		if (pageable.getPageSize() < 1 || pageable.getPageSize() > MAX_PAGE_SIZE) {
			throw new IllegalArgumentException("Page size must be between 1 and " + MAX_PAGE_SIZE + ".");
		}
	}
}
