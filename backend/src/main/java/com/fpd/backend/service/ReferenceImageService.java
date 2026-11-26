package com.fpd.backend.service;

import java.util.List;
import java.util.Locale;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.fpd.backend.config.ReferenceStorageProperties;
import com.fpd.backend.dto.response.ReferenceImageResponseDto;
import com.fpd.backend.dto.response.VisualReferenceImageDto;
import com.fpd.backend.entity.ProductReferenceImage;
import com.fpd.backend.entity.ProductReferenceImage.ImageType;
import com.fpd.backend.entity.ProductVersion;
import com.fpd.backend.exception.ImageValidationException;
import com.fpd.backend.exception.ReferenceNotFoundException;
import com.fpd.backend.repository.ProductReferenceImageRepository;
import com.fpd.backend.repository.ProductVersionRepository;
import com.fpd.backend.storage.ReferenceImageStorage;

@Service
public class ReferenceImageService {
	private final ProductVersionRepository versionRepository;
	private final ProductReferenceImageRepository imageRepository;
	private final ReferenceImageStorage storage;
	private final ReferenceStorageProperties storageProperties;
	private final ImageUploadValidator uploadValidator;

	public ReferenceImageService(ProductVersionRepository versionRepository,
			ProductReferenceImageRepository imageRepository,
			ReferenceImageStorage storage,
			ReferenceStorageProperties storageProperties,
			ImageUploadValidator uploadValidator) {
		this.versionRepository = versionRepository;
		this.imageRepository = imageRepository;
		this.storage = storage;
		this.storageProperties = storageProperties;
		this.uploadValidator = uploadValidator;
	}

	@Transactional
	public ReferenceImageResponseDto upload(Long versionId, MultipartFile file,
			ImageType imageType, String viewType) {
		ProductVersion version = requireVersion(versionId);
		validate(file);
		String extension = extensionFor(file.getContentType());
		String safeName = sanitizeFilename(file.getOriginalFilename());
		String key = "references/" + versionId + "/" + UUID.randomUUID() + "." + extension;

		ReferenceImageStorage.StoredImage stored;
		try {
			stored = storage.store(key, file.getContentType(), file.getSize(), file.getInputStream());
		}
		catch (java.io.IOException exception) {
			throw new ImageValidationException("Reference image could not be read.");
		}

		ProductReferenceImage image = imageRepository.save(new ProductReferenceImage(
				version, stored.storageKey(), stored.imageUrl(), imageType,
				viewType, safeName, file.getContentType(), file.getSize()));
		return map(image);
	}

	public List<ReferenceImageResponseDto> findByVersion(Long versionId) {
		requireVersion(versionId);
		return imageRepository.findByProductVersionIdOrderByIdAsc(versionId)
				.stream().map(this::map).toList();
	}

	public ReferenceImageResponseDto findById(Long imageId) {
		return map(requireImage(imageId));
	}

	@Transactional
	public ReferenceImageResponseDto updateContent(Long imageId, MultipartFile file) {
		ProductReferenceImage image = requireImage(imageId);
		validate(file);
		try {
			storage.store(image.getStorageKey(), file.getContentType(),
					file.getSize(), file.getInputStream());
		}
		catch (java.io.IOException exception) {
			throw new ImageValidationException("Reference image could not be read.");
		}
		image.updateStoredContent(
				image.getStorageKey(),
				image.getImageUrl(),
				sanitizeFilename(file.getOriginalFilename()),
				file.getContentType(),
				file.getSize());
		return map(imageRepository.save(image));
	}

	@Transactional(readOnly = true)
	public List<VisualReferenceImageDto> findVisualReferences() {
		return imageRepository.findAll().stream()
				.map(image -> {
					boolean available = storage.exists(image.getStorageKey());
					long lastModified = available
							? storage.lastModifiedNanos(image.getStorageKey())
							: 0L;
					return new VisualReferenceImageDto(
							image.getId(),
							image.getProductVersion().getProduct().getId(),
							image.getProductVersion().getProduct().getBrand(),
							image.getProductVersion().getProduct().getProductName(),
							image.getProductVersion().getProduct().getExpectedText(),
							image.getProductVersion().getProduct().getBarcode(),
							image.getImageType().name(),
							image.getContentType(),
							image.getFileSize(),
							lastModified,
							available);
				})
				.toList();
	}

	public byte[] readContent(Long imageId) {
		ProductReferenceImage image = requireImage(imageId);
		if (!storage.exists(image.getStorageKey())) {
			throw new ReferenceNotFoundException(
					"Reference image content with id " + imageId + " was not found.");
		}
		return storage.read(image.getStorageKey());
	}

	@Transactional
	public void delete(Long imageId) {
		ProductReferenceImage image = requireImage(imageId);
		storage.delete(image.getStorageKey());
		imageRepository.delete(image);
	}

	private void validate(MultipartFile file) {
		if (file == null || file.isEmpty()) {
			throw new ImageValidationException("The uploaded image is empty.");
		}
		uploadValidator.validate(file, storageProperties.getMaxFileSize());
	}

	private String extensionFor(String contentType) {
		return switch (contentType.toLowerCase(Locale.ROOT)) {
			case "image/jpeg" -> "jpg";
			case "image/webp" -> "webp";
			default -> "png";
		};
	}

	private String sanitizeFilename(String filename) {
		if (filename == null) {
			return "image";
		}
		String name = filename.replace('\\', '/');
		int slash = name.lastIndexOf('/');
		name = name.substring(slash + 1);
		name = name.replaceAll("[^A-Za-z0-9._-]", "_");
		if (name.isBlank() || ".".equals(name) || "..".equals(name)) {
			return "image";
		}
		return name.substring(0, Math.min(name.length(), 255));
	}

	private ProductVersion requireVersion(Long versionId) {
		return versionRepository.findById(versionId)
				.orElseThrow(() -> new ReferenceNotFoundException(
						"Product version with id " + versionId + " was not found."));
	}

	private ProductReferenceImage requireImage(Long imageId) {
		return imageRepository.findById(imageId)
				.orElseThrow(() -> new ReferenceNotFoundException(
						"Reference image with id " + imageId + " was not found."));
	}

	private ReferenceImageResponseDto map(ProductReferenceImage image) {
		return new ReferenceImageResponseDto(
				image.getId(), image.getProductVersion().getId(),
				image.getImageUrl(), image.getStorageKey(), image.getImageType(),
				image.getViewType(), image.getOriginalFilename(),
				image.getContentType(), image.getFileSize(), image.getCreatedAt());
	}
}
