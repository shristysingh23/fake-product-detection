package com.fpd.backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fpd.backend.entity.ProductVersion;

public interface ProductVersionRepository extends JpaRepository<ProductVersion, Long> {
	List<ProductVersion> findByProductIdOrderByIdAsc(Long productId);
	boolean existsByProductIdAndVersionCodeIgnoreCase(Long productId, String versionCode);
	boolean existsByProductIdAndVersionCodeIgnoreCaseAndIdNot(
			Long productId, String versionCode, Long id);
}
