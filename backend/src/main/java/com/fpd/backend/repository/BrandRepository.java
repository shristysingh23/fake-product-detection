package com.fpd.backend.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fpd.backend.entity.Brand;

public interface BrandRepository extends JpaRepository<Brand, Long> {
	Optional<Brand> findByNameIgnoreCase(String name);
	boolean existsByNameIgnoreCase(String name);
}
