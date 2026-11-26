package com.fpd.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fpd.backend.entity.Product;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface ProductRepository extends JpaRepository<Product, Long> {
	List<Product> findByBrandReferenceId(Long brandId);
	Page<Product> findByBrandReferenceId(Long brandId, Pageable pageable);
	boolean existsByBrandReferenceId(Long brandId);
}
