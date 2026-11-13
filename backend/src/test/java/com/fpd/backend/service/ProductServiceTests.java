package com.fpd.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.test.util.ReflectionTestUtils;

import com.fpd.backend.dto.request.ProductCreateRequestDto;
import com.fpd.backend.dto.request.ProductUpdateRequestDto;
import com.fpd.backend.dto.response.ProductResponseDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.exception.ProductNotFoundException;
import com.fpd.backend.repository.ProductRepository;

class ProductServiceTests {

	private ProductRepository productRepository;
	private ProductService productService;

	@BeforeEach
	void setUp() {
		productRepository = org.mockito.Mockito.mock(ProductRepository.class);
		productService = new ProductService(productRepository);
	}

	@Test
	void createsProductAndMapsSavedProduct() {
		ProductCreateRequestDto request = new ProductCreateRequestDto(
				"Acme", "Original Cereal", "Food", "0012345678905", "Genuine product text");
		when(productRepository.save(any(Product.class))).thenAnswer(invocation -> {
			Product product = invocation.getArgument(0);
			ReflectionTestUtils.setField(product, "id", 11L);
			return product;
		});

		ProductResponseDto response = productService.createProduct(request);

		ArgumentCaptor<Product> savedProduct = ArgumentCaptor.forClass(Product.class);
		verify(productRepository).save(savedProduct.capture());
		assertProduct(savedProduct.getValue(), 11L, "Acme", "Original Cereal", "Food",
				"0012345678905", "Genuine product text");
		assertEquals(responseDto(11L, "Acme", "Original Cereal", "Food",
				"0012345678905", "Genuine product text"), response);
	}

	@Test
	void getsProductById() {
		Product product = product(21L, "Acme", "Original Cereal", "Food", "0012345678905", "Genuine text");
		when(productRepository.findById(21L)).thenReturn(Optional.of(product));

		ProductResponseDto response = productService.getProductById(21L);

		assertEquals(responseDto(21L, "Acme", "Original Cereal", "Food",
				"0012345678905", "Genuine text"), response);
		verify(productRepository).findById(21L);
	}

	@Test
	void throwsWhenProductByIdDoesNotExist() {
		when(productRepository.findById(404L)).thenReturn(Optional.empty());

		ProductNotFoundException exception = assertThrows(
				ProductNotFoundException.class, () -> productService.getProductById(404L));

		assertEquals("Product with id 404 was not found.", exception.getMessage());
	}

	@Test
	void getsAllProducts() {
		Product first = product(1L, "Acme", "Cereal", "Food", null, null);
		Product second = product(2L, "Baker Co.", "Bread", "Bakery", "0002", "Genuine bread");
		when(productRepository.findAll()).thenReturn(List.of(first, second));

		List<ProductResponseDto> response = productService.getAllProducts();

		assertEquals(List.of(
				responseDto(1L, "Acme", "Cereal", "Food", null, null),
				responseDto(2L, "Baker Co.", "Bread", "Bakery", "0002", "Genuine bread")), response);
		verify(productRepository).findAll();
	}

	@Test
	void forwardsPageableToRepository() {
		Pageable pageable = PageRequest.of(2, 5, Sort.by("brand").descending());
		when(productRepository.findAll(pageable)).thenReturn(Page.empty(pageable));

		productService.getAllProducts(pageable);

		verify(productRepository).findAll(pageable);
	}

	@Test
	void mapsPageContentAndPreservesPaginationMetadata() {
		Pageable pageable = PageRequest.of(1, 2, Sort.by("id").ascending());
		Page<Product> productPage = new PageImpl<>(List.of(
				product(3L, "Acme", "Cereal", "Food", "0003", "Text 3"),
				product(4L, "Baker Co.", "Bread", "Bakery", "0004", "Text 4")), pageable, 5);
		when(productRepository.findAll(pageable)).thenReturn(productPage);

		Page<ProductResponseDto> responsePage = productService.getAllProducts(pageable);

		assertEquals(List.of(
				responseDto(3L, "Acme", "Cereal", "Food", "0003", "Text 3"),
				responseDto(4L, "Baker Co.", "Bread", "Bakery", "0004", "Text 4")),
				responsePage.getContent());
		assertEquals(1, responsePage.getNumber());
		assertEquals(2, responsePage.getSize());
		assertEquals(5, responsePage.getTotalElements());
		assertEquals(3, responsePage.getTotalPages());
		assertEquals(pageable, responsePage.getPageable());
	}

	@Test
	void returnsEmptyPageWithPaginationMetadata() {
		Pageable pageable = PageRequest.of(2, 10, Sort.by("id").ascending());
		when(productRepository.findAll(pageable)).thenReturn(Page.empty(pageable));

		Page<ProductResponseDto> responsePage = productService.getAllProducts(pageable);

		assertTrue(responsePage.isEmpty());
		assertEquals(2, responsePage.getNumber());
		assertEquals(10, responsePage.getSize());
		assertEquals(0, responsePage.getTotalElements());
		verify(productRepository).findAll(pageable);
	}

	@Test
	void appliesIdAscendingSortWhenPageableIsUnsorted() {
		Pageable pageable = PageRequest.of(0, 10);
		Pageable sortedPageable = PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "id"));
		when(productRepository.findAll(sortedPageable)).thenReturn(Page.empty(sortedPageable));

		productService.getAllProducts(pageable);

		verify(productRepository).findAll(sortedPageable);
	}

	@Test
	void rejectsPageSizeAboveMaximum() {
		Pageable pageable = PageRequest.of(0, 101);

		assertThrows(IllegalArgumentException.class, () -> productService.getAllProducts(pageable));

		verifyNoInteractions(productRepository);
	}

	@Test
	void rejectsPageSizeBelowMinimum() {
		Pageable pageable = org.mockito.Mockito.mock(Pageable.class);
		when(pageable.isUnpaged()).thenReturn(false);
		when(pageable.getPageNumber()).thenReturn(0);
		when(pageable.getPageSize()).thenReturn(0);

		assertThrows(IllegalArgumentException.class, () -> productService.getAllProducts(pageable));

		verifyNoInteractions(productRepository);
	}

	@Test
	void rejectsNegativePageNumber() {
		Pageable pageable = org.mockito.Mockito.mock(Pageable.class);
		when(pageable.isUnpaged()).thenReturn(false);
		when(pageable.getPageNumber()).thenReturn(-1);

		assertThrows(IllegalArgumentException.class, () -> productService.getAllProducts(pageable));

		verifyNoInteractions(productRepository);
	}

	@Test
	void updatesAllProductFields() {
		Product product = product(31L, "Old Brand", "Old Name", "Old Category", "old-barcode", "Old text");
		ProductUpdateRequestDto request = new ProductUpdateRequestDto(
				"New Brand", "New Name", "New Category", null, null);
		when(productRepository.findById(31L)).thenReturn(Optional.of(product));
		when(productRepository.save(product)).thenReturn(product);

		ProductResponseDto response = productService.updateProduct(31L, request);

		assertProduct(product, 31L, "New Brand", "New Name", "New Category", null, null);
		assertEquals(responseDto(31L, "New Brand", "New Name", "New Category", null, null), response);
		verify(productRepository).save(product);
	}

	@Test
	void throwsWhenUpdatingProductThatDoesNotExist() {
		when(productRepository.findById(404L)).thenReturn(Optional.empty());
		ProductUpdateRequestDto request = new ProductUpdateRequestDto(
				"Brand", "Name", "Category", null, null);

		ProductNotFoundException exception = assertThrows(
				ProductNotFoundException.class, () -> productService.updateProduct(404L, request));

		assertEquals("Product with id 404 was not found.", exception.getMessage());
		verify(productRepository, never()).save(any(Product.class));
	}

	@Test
	void deletesExistingProduct() {
		Product product = product(41L, "Acme", "Cereal", "Food", null, null);
		when(productRepository.findById(41L)).thenReturn(Optional.of(product));

		productService.deleteProduct(41L);

		verify(productRepository).delete(product);
	}

	@Test
	void throwsWhenDeletingProductThatDoesNotExist() {
		when(productRepository.findById(404L)).thenReturn(Optional.empty());

		ProductNotFoundException exception = assertThrows(
				ProductNotFoundException.class, () -> productService.deleteProduct(404L));

		assertEquals("Product with id 404 was not found.", exception.getMessage());
		verify(productRepository, never()).delete(any(Product.class));
	}

	private Product product(Long id, String brand, String productName, String category,
			String barcode, String expectedText) {
		Product product = new Product(brand, productName, category, barcode, expectedText);
		ReflectionTestUtils.setField(product, "id", id);
		return product;
	}

	private ProductResponseDto responseDto(Long id, String brand, String productName, String category,
			String barcode, String expectedText) {
		return new ProductResponseDto(id, brand, productName, category, barcode, expectedText);
	}

	private void assertProduct(Product product, Long id, String brand, String productName, String category,
			String barcode, String expectedText) {
		assertEquals(id, product.getId());
		assertEquals(brand, product.getBrand());
		assertEquals(productName, product.getProductName());
		assertEquals(category, product.getCategory());
		assertEquals(barcode, product.getBarcode());
		assertEquals(expectedText, product.getExpectedText());
	}
}
