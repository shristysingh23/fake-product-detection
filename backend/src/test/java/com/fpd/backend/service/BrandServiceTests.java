package com.fpd.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import com.fpd.backend.dto.request.BrandCreateRequestDto;
import com.fpd.backend.dto.request.BrandUpdateRequestDto;
import com.fpd.backend.entity.Brand;
import com.fpd.backend.exception.BrandNotFoundException;
import com.fpd.backend.exception.DuplicateReferenceException;
import com.fpd.backend.repository.BrandRepository;
import com.fpd.backend.repository.ProductRepository;

class BrandServiceTests {
	private BrandRepository brandRepository;
	private ProductRepository productRepository;
	private BrandService service;

	@BeforeEach
	void setUp() {
		brandRepository = org.mockito.Mockito.mock(BrandRepository.class);
		productRepository = org.mockito.Mockito.mock(ProductRepository.class);
		service = new BrandService(brandRepository, productRepository);
	}

	@Test
	void createsBrand() {
		when(brandRepository.existsByNameIgnoreCase("Adidas")).thenReturn(false);
		when(brandRepository.save(any(Brand.class))).thenAnswer(invocation -> {
			Brand brand = invocation.getArgument(0);
			ReflectionTestUtils.setField(brand, "id", 1L);
			return brand;
		});

		var response = service.create(new BrandCreateRequestDto(
				" Adidas ", "Sportswear", "https://adidas.example", "Germany"));

		assertEquals(1L, response.id());
		assertEquals("Adidas", response.name());
		verify(brandRepository).save(any(Brand.class));
	}

	@Test
	void listsAndRetrievesBrands() {
		Brand brand = brand(1L, "Adidas");
		when(brandRepository.findAll()).thenReturn(List.of(brand));
		when(brandRepository.findById(1L)).thenReturn(Optional.of(brand));

		assertEquals("Adidas", service.findAll().get(0).name());
		assertEquals("Adidas", service.findById(1L).name());
	}

	@Test
	void updatesBrand() {
		Brand brand = brand(1L, "Old Name");
		when(brandRepository.findById(1L)).thenReturn(Optional.of(brand));
		when(brandRepository.findByNameIgnoreCase("New Name")).thenReturn(Optional.empty());
		when(brandRepository.save(brand)).thenReturn(brand);

		var result = service.update(1L,
				new BrandUpdateRequestDto("New Name", "Updated", null, "US"));

		assertEquals("New Name", result.name());
		assertEquals("Updated", result.description());
	}

	@Test
	void rejectsDuplicateBrandNames() {
		when(brandRepository.existsByNameIgnoreCase("Adidas")).thenReturn(true);

		assertThrows(DuplicateReferenceException.class, () -> service.create(
				new BrandCreateRequestDto("Adidas", null, null, null)));

		verify(brandRepository, never()).save(any(Brand.class));
	}

	@Test
	void refusesDeletingBrandWithProducts() {
		when(brandRepository.findById(1L)).thenReturn(Optional.of(brand(1L, "Adidas")));
		when(productRepository.existsByBrandReferenceId(1L)).thenReturn(true);

		assertThrows(DuplicateReferenceException.class, () -> service.delete(1L));
	}

	@Test
	void returnsNotFoundForMissingBrand() {
		when(brandRepository.findById(404L)).thenReturn(Optional.empty());

		assertThrows(BrandNotFoundException.class, () -> service.findById(404L));
	}

	private Brand brand(long id, String name) {
		Brand brand = new Brand(name, "Description", null, "Germany");
		ReflectionTestUtils.setField(brand, "id", id);
		return brand;
	}
}
