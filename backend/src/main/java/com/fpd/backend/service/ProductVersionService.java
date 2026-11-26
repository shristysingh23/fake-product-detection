package com.fpd.backend.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fpd.backend.dto.request.ProductVersionRequestDto;
import com.fpd.backend.dto.response.ProductVersionResponseDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.entity.ProductVersion;
import com.fpd.backend.exception.DuplicateReferenceException;
import com.fpd.backend.exception.ProductNotFoundException;
import com.fpd.backend.exception.ReferenceNotFoundException;
import com.fpd.backend.repository.ProductRepository;
import com.fpd.backend.repository.ProductVersionRepository;
import com.fpd.backend.repository.ProductReferenceImageRepository;

@Service
public class ProductVersionService {
	private final ProductRepository productRepository;
	private final ProductVersionRepository versionRepository;
	private final ProductReferenceImageRepository imageRepository;

	public ProductVersionService(ProductRepository productRepository,
			ProductVersionRepository versionRepository,
			ProductReferenceImageRepository imageRepository) {
		this.productRepository = productRepository;
		this.versionRepository = versionRepository;
		this.imageRepository = imageRepository;
	}

	@Transactional
	public ProductVersionResponseDto create(Long productId, ProductVersionRequestDto request) {
		Product product = requireProduct(productId);
		if (versionRepository.existsByProductIdAndVersionCodeIgnoreCase(
				productId, request.versionCode().trim())) {
			throw new DuplicateReferenceException(
					"A version code already exists for this product.");
		}
		ProductVersion version = versionRepository.save(new ProductVersion(
				product, request.versionName().trim(), request.versionCode().trim(),
				request.releaseDate(), request.description(),
				request.packagingDetails(), request.active() == null || request.active()));
		return map(version);
	}

	public List<ProductVersionResponseDto> findByProduct(Long productId) {
		requireProduct(productId);
		return versionRepository.findByProductIdOrderByIdAsc(productId)
				.stream().map(this::map).toList();
	}

	public ProductVersionResponseDto findById(Long versionId) {
		return map(requireVersion(versionId));
	}

	@Transactional
	public ProductVersionResponseDto update(Long versionId, ProductVersionRequestDto request) {
		ProductVersion version = requireVersion(versionId);
		Long productId = version.getProduct().getId();
		if (versionRepository.existsByProductIdAndVersionCodeIgnoreCaseAndIdNot(
				productId, request.versionCode().trim(), versionId)) {
			throw new DuplicateReferenceException(
					"A version code already exists for this product.");
		}
		version.update(request.versionName().trim(), request.versionCode().trim(),
				request.releaseDate(), request.description(),
				request.packagingDetails(), request.active() == null || request.active());
		return map(versionRepository.save(version));
	}

	@Transactional
	public void delete(Long versionId) {
		ProductVersion version = requireVersion(versionId);
		if (imageRepository.countByProductVersionId(versionId) > 0) {
			throw new DuplicateReferenceException(
					"Product version cannot be deleted because reference images depend on it.");
		}
		versionRepository.delete(version);
	}

	private Product requireProduct(Long productId) {
		return productRepository.findById(productId)
				.orElseThrow(() -> new ProductNotFoundException(
						"Product with id " + productId + " was not found."));
	}

	private ProductVersion requireVersion(Long versionId) {
		return versionRepository.findById(versionId)
				.orElseThrow(() -> new ReferenceNotFoundException(
						"Product version with id " + versionId + " was not found."));
	}

	private ProductVersionResponseDto map(ProductVersion version) {
		return new ProductVersionResponseDto(
				version.getId(), version.getProduct().getId(),
				version.getVersionName(), version.getVersionCode(),
				version.getReleaseDate(), version.getDescription(),
				version.getPackagingDetails(), version.isActive(),
				version.getCreatedAt(), version.getUpdatedAt());
	}
}
