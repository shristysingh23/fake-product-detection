package com.fpd.backend.entity;

import java.time.Instant;
import java.time.LocalDate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Entity
@Table(name = "product_versions",
	uniqueConstraints = @UniqueConstraint(name = "uk_product_version_code",
			columnNames = {"product_id", "version_code"}))
public class ProductVersion {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@ManyToOne(fetch = FetchType.LAZY, optional = false)
	@JoinColumn(name = "product_id", nullable = false)
	private Product product;

	@NotBlank
	@Size(max = 200)
	@Column(name = "version_name", nullable = false, length = 200)
	private String versionName;

	@NotBlank
	@Size(max = 100)
	@Column(name = "version_code", nullable = false, length = 100)
	private String versionCode;

	@Column(name = "release_date")
	private LocalDate releaseDate;

	@Column(columnDefinition = "text")
	private String description;

	@Column(name = "packaging_details", columnDefinition = "text")
	private String packagingDetails;

	@Column(name = "is_active", nullable = false)
	private boolean active = true;

	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt;

	@Column(name = "updated_at", nullable = false)
	private Instant updatedAt;

	protected ProductVersion() {
	}

	public ProductVersion(Product product, String versionName, String versionCode,
			LocalDate releaseDate, String description, String packagingDetails, boolean active) {
		this.product = product;
		this.versionName = versionName;
		this.versionCode = versionCode;
		this.releaseDate = releaseDate;
		this.description = description;
		this.packagingDetails = packagingDetails;
		this.active = active;
		Instant now = Instant.now();
		this.createdAt = now;
		this.updatedAt = now;
	}

	public void update(String versionName, String versionCode, LocalDate releaseDate,
			String description, String packagingDetails, boolean active) {
		this.versionName = versionName;
		this.versionCode = versionCode;
		this.releaseDate = releaseDate;
		this.description = description;
		this.packagingDetails = packagingDetails;
		this.active = active;
		this.updatedAt = Instant.now();
	}

	public Long getId() { return id; }
	public Product getProduct() { return product; }
	public String getVersionName() { return versionName; }
	public String getVersionCode() { return versionCode; }
	public LocalDate getReleaseDate() { return releaseDate; }
	public String getDescription() { return description; }
	public String getPackagingDetails() { return packagingDetails; }
	public boolean isActive() { return active; }
	public Instant getCreatedAt() { return createdAt; }
	public Instant getUpdatedAt() { return updatedAt; }
}
