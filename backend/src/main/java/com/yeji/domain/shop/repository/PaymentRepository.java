package com.yeji.domain.shop.repository;

import com.yeji.domain.shop.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PaymentRepository extends JpaRepository<Payment, String> {
    List<Payment> findAllByUserIdOrderByCreatedAtDesc(Long userId);
}