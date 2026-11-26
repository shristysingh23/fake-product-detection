package com.fpd.backend.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "product_reference_images")
public class ProductReferenceImage {

	public enum ImageType {
		FRONT, BACK, LEFT, RIGHT, TOP, BOTTOM, LOGO, LABEL, BARCODE
	}

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "product_version_id", nullable = false)
	private ProductVersion productVersion;

	@Column(name = "storage_key", nullable = false, length = 1000)
	private String storageKey;

	@Column(name = "image_url", length = 1000)
	private String imageUrl;

	@Enumerated(EnumType.STRING)
	@Column(name = "image_type", nullable = false, length = 20)
	private ImageType imageType;

	@Column(name = "view_type", length = 100)
	private String viewType;

	@Column(name = "original_filename", nullable = false, length = 255)
	private String originalFilename;

	@Column(name = "content_type", nullable = false, length = 100)
	private String contentType;

	@Column(name = "file_size", nullable = false)
	private long fileSize;

	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt;

	protected ProductReferenceImage() {
	}

	public ProductReferenceImage(ProductVersion productVersion, String storageKey, String imageUrl,
			ImageType imageType, String viewType, String originalFilename,
			String contentType, long fileSize) {
		this.productVersion = productVersion;
		this.storageKey = storageKey;
		this.imageUrl = imageUrl;
		this.imageType = imageType;
		this.viewType = viewType;
		this.originalFilename = originalFilename;
		this.contentType = contentType;
		this.fileSize = fileSize;
		this.createdAt = Instant.now();
	}

	public void updateStoredContent(String storageKey, String imageUrl,
			String originalFilename, String contentType, long fileSize) {
		this.storageKey = storageKey;
		this.imageUrl = imageUrl;
		this.originalFilename = originalFilename;
		this.contentType = contentType;
		this.fileSize = fileSize;
	}

	public Long getId() { return id; }
	public ProductVersion getProductVersion() { return productVersion; }
	public String getStorageKey() { return storageKey; }
	public String getImageUrl() { return imageUrl; }
	public ImageType getImageType() { return imageType; }
	public String getViewType() { return viewType; }
	public String getOriginalFilename() { return originalFilename; }
	public String getContentType() { return contentType; }
	public long getFileSize() { return fileSize; }
	public Instant getCreatedAt() { return createdAt; }
}
