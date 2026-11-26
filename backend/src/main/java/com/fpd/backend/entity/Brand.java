package com.fpd.backend.entity;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Entity
@Table(name = "brands")
public class Brand {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@NotBlank
	@Size(max = 200)
	@Column(nullable = false, unique = true, length = 200)
	private String name;

	@Column(columnDefinition = "text")
	private String description;

	@Size(max = 500)
	@Column(name = "official_website", length = 500)
	private String officialWebsite;

	@Size(max = 100)
	@Column(length = 100)
	private String country;

	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt;

	@Column(name = "updated_at", nullable = false)
	private Instant updatedAt;

	protected Brand() {
	}

	public Brand(String name, String description, String officialWebsite, String country) {
		this.name = name;
		this.description = description;
		this.officialWebsite = officialWebsite;
		this.country = country;
		Instant now = Instant.now();
		this.createdAt = now;
		this.updatedAt = now;
	}

	public void update(String name, String description, String officialWebsite, String country) {
		this.name = name;
		this.description = description;
		this.officialWebsite = officialWebsite;
		this.country = country;
		this.updatedAt = Instant.now();
	}

	public Long getId() { return id; }
	public String getName() { return name; }
	public String getDescription() { return description; }
	public String getOfficialWebsite() { return officialWebsite; }
	public String getCountry() { return country; }
	public Instant getCreatedAt() { return createdAt; }
	public Instant getUpdatedAt() { return updatedAt; }
}
