package com.fpd.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import com.fpd.backend.dto.request.ProductVersionRequestDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.entity.ProductVersion;
import com.fpd.backend.exception.DuplicateReferenceException;
import com.fpd.backend.exception.ProductNotFoundException;
import com.fpd.backend.exception.ReferenceNotFoundException;
import com.fpd.backend.repository.ProductReferenceImageRepository;
import com.fpd.backend.repository.ProductRepository;
import com.fpd.backend.repository.ProductVersionRepository;

class ProductVersionServiceTests {
	private ProductRepository productRepository;
	private ProductVersionRepository versionRepository;
	private ProductReferenceImageRepository imageRepository;
	private ProductVersionService service;

	@BeforeEach
	void setUp() {
		productRepository = org.mockito.Mockito.mock(ProductRepository.class);
		versionRepository = org.mockito.Mockito.mock(ProductVersionRepository.class);
		imageRepository = org.mockito.Mockito.mock(ProductReferenceImageRepository.class);
		service = new ProductVersionService(productRepository, versionRepository, imageRepository);
	}

	@Test
	void createsListsAndRetrievesVersion() {
		Product product = product(2L);
		ProductVersion version = version(product, "2025", "v2");
		when(productRepository.findById(2L)).thenReturn(Optional.of(product));
		when(versionRepository.existsByProductIdAndVersionCodeIgnoreCase(2L, "v2"))
				.thenReturn(false);
		when(versionRepository.save(any(ProductVersion.class))).thenAnswer(invocation -> {
			ProductVersion saved = invocation.getArgument(0);
			ReflectionTestUtils.setField(saved, "id", 5L);
			return saved;
		});
		when(versionRepository.findByProductIdOrderByIdAsc(2L)).thenReturn(List.of(version));
		when(versionRepository.findById(5L)).thenReturn(Optional.of(version));

		var created = service.create(2L, request("2025", "v2"));

		assertEquals(2L, created.productId());
		assertEquals("v2", created.versionCode());
		assertEquals(1, service.findByProduct(2L).size());
		assertEquals("2025", service.findById(5L).versionName());
	}

	@Test
	void updatesAndDeletesVersion() {
		ProductVersion version = version(product(2L), "2024", "v1");
		when(versionRepository.findById(5L)).thenReturn(Optional.of(version));
		when(versionRepository.existsByProductIdAndVersionCodeIgnoreCaseAndIdNot(2L, "v2", 5L))
				.thenReturn(false);
		when(versionRepository.save(version)).thenReturn(version);
		when(imageRepository.countByProductVersionId(5L)).thenReturn(0L);

		assertEquals("2025", service.update(5L, request("2025", "v2")).versionName());
		service.delete(5L);
		verify(versionRepository).delete(version);
	}

	@Test
	void rejectsDuplicateVersionCode() {
		when(productRepository.findById(2L)).thenReturn(Optional.of(product(2L)));
		when(versionRepository.existsByProductIdAndVersionCodeIgnoreCase(2L, "v1"))
				.thenReturn(true);

		assertThrows(DuplicateReferenceException.class,
				() -> service.create(2L, request("2024", "v1")));

		verify(versionRepository, never()).save(any(ProductVersion.class));
	}

	@Test
	void rejectsInvalidProductAndMissingVersion() {
		when(productRepository.findById(404L)).thenReturn(Optional.empty());
		when(versionRepository.findById(404L)).thenReturn(Optional.empty());

		assertThrows(ProductNotFoundException.class,
				() -> service.create(404L, request("2025", "v2")));
		assertThrows(ReferenceNotFoundException.class, () -> service.findById(404L));
	}

	@Test
	void refusesDeletingVersionWithReferenceImages() {
		ProductVersion version = version(product(2L), "2024", "v1");
		ReflectionTestUtils.setField(version, "id", 5L);
		when(versionRepository.findById(5L)).thenReturn(Optional.of(version));
		when(imageRepository.countByProductVersionId(5L)).thenReturn(1L);

		assertThrows(DuplicateReferenceException.class, () -> service.delete(5L));
		verify(versionRepository, never()).delete(version);
	}

	private ProductVersionRequestDto request(String name, String code) {
		return new ProductVersionRequestDto(name, code,
				LocalDate.of(2025, 1, 1), null, null, true);
	}

	private Product product(long id) {
		Product product = new Product("Adidas", "Ultraboost", "Shoes", null, null);
		ReflectionTestUtils.setField(product, "id", id);
		return product;
	}

	private ProductVersion version(Product product, String name, String code) {
		ProductVersion version = new ProductVersion(
				product, name, code, LocalDate.of(2025, 1, 1), null, null, true);
		ReflectionTestUtils.setField(version, "id", 5L);
		return version;
	}
}
