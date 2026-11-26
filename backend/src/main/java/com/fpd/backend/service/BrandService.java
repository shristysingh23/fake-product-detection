package com.fpd.backend.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fpd.backend.dto.request.BrandCreateRequestDto;
import com.fpd.backend.dto.request.BrandUpdateRequestDto;
import com.fpd.backend.dto.response.BrandResponseDto;
import com.fpd.backend.entity.Brand;
import com.fpd.backend.exception.BrandNotFoundException;
import com.fpd.backend.exception.DuplicateReferenceException;
import com.fpd.backend.repository.BrandRepository;
import com.fpd.backend.repository.ProductRepository;

@Service
public class BrandService {
	private final BrandRepository brandRepository;
	private final ProductRepository productRepository;

	public BrandService(BrandRepository brandRepository, ProductRepository productRepository) {
		this.brandRepository = brandRepository;
		this.productRepository = productRepository;
	}

	@Transactional
	public BrandResponseDto create(BrandCreateRequestDto request) {
		if (brandRepository.existsByNameIgnoreCase(request.name().trim())) {
			throw new DuplicateReferenceException("A brand with this name already exists.");
		}
		Brand brand = brandRepository.save(new Brand(
				request.name().trim(), request.description(),
				request.officialWebsite(), request.country()));
		return map(brand);
	}

	public List<BrandResponseDto> findAll() {
		return brandRepository.findAll().stream().map(this::map).toList();
	}

	public BrandResponseDto findById(Long id) {
		return map(requireBrand(id));
	}

	@Transactional
	public BrandResponseDto update(Long id, BrandUpdateRequestDto request) {
		Brand brand = requireBrand(id);
		brandRepository.findByNameIgnoreCase(request.name().trim())
				.filter(existing -> !existing.getId().equals(id))
				.ifPresent(existing -> {
					throw new DuplicateReferenceException("A brand with this name already exists.");
				});
		brand.update(request.name().trim(), request.description(),
				request.officialWebsite(), request.country());
		return map(brandRepository.save(brand));
	}

	@Transactional
	public void delete(Long id) {
		Brand brand = requireBrand(id);
		if (productRepository.existsByBrandReferenceId(id)) {
			throw new DuplicateReferenceException(
					"Brand cannot be deleted because products depend on it.");
		}
		brandRepository.delete(brand);
	}

	private Brand requireBrand(Long id) {
		return brandRepository.findById(id)
				.orElseThrow(() -> new BrandNotFoundException(
						"Brand with id " + id + " was not found."));
	}

	private BrandResponseDto map(Brand brand) {
		return new BrandResponseDto(brand.getId(), brand.getName(), brand.getDescription(),
				brand.getOfficialWebsite(), brand.getCountry(),
				brand.getCreatedAt(), brand.getUpdatedAt());
	}
}
