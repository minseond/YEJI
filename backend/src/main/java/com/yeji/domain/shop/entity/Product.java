package com.yeji.domain.shop.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@Table(name = "products")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "product_id")
    private Integer id;

    @Column(name = "name", length = 100)
    private String name;

    @Column(name = "price_krw", nullable = false)
    private Integer priceKrw;

    @Column(name = "fp_amount", nullable = false)
    private Integer fpAmount;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive;

    @Builder
    public Product(String name, Integer priceKrw, Integer fpAmount, Boolean isActive) {
        this.name = name;
        this.priceKrw = priceKrw;
        this.fpAmount = fpAmount;
        this.isActive = isActive;
    }
}