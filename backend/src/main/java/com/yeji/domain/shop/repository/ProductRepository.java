package com.yeji.domain.shop.repository;

import com.yeji.domain.shop.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ProductRepository extends JpaRepository<Product, Integer> {
    // 판매 중인 상품만 조회
    List<Product> findAllByIsActiveTrue();
}