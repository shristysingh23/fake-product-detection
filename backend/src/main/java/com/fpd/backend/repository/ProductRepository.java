package com.fpd.backend.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fpd.backend.entity.Product;

public interface ProductRepository extends JpaRepository<Product, Long> {
}
