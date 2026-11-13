package com.fpd.backend.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Entity
@Table(name = "products")
public class Product {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@NotBlank
	@Size(max = 120)
	@Column(name = "brand", nullable = false, length = 120)
	private String brand;

	@NotBlank
	@Size(max = 200)
	@Column(name = "product_name", nullable = false, length = 200)
	private String productName;

	@NotBlank
	@Size(max = 100)
	@Column(name = "category", nullable = false, length = 100)
	private String category;

	@Size(max = 64)
	@Column(name = "barcode", length = 64)
	private String barcode;

	@Size(max = 5000)
	@Column(name = "expected_text", columnDefinition = "text")
	private String expectedText;

	protected Product() {
	}

	public Long getId() {
		return id;
	}

	public String getBrand() {
		return brand;
	}

	public void setBrand(String brand) {
		this.brand = brand;
	}

	public String getProductName() {
		return productName;
	}

	public void setProductName(String productName) {
		this.productName = productName;
	}

	public String getCategory() {
		return category;
	}

	public void setCategory(String category) {
		this.category = category;
	}

	public String getBarcode() {
		return barcode;
	}

	public void setBarcode(String barcode) {
		this.barcode = barcode;
	}

	public String getExpectedText() {
		return expectedText;
	}

	public void setExpectedText(String expectedText) {
		this.expectedText = expectedText;
	}
}
