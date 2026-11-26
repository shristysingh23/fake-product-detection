package com.fpd.backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fpd.backend.entity.ProductReferenceImage;

public interface ProductReferenceImageRepository extends JpaRepository<ProductReferenceImage, Long> {
	List<ProductReferenceImage> findByProductVersionIdOrderByIdAsc(Long productVersionId);
	long countByProductVersionId(Long productVersionId);
}
