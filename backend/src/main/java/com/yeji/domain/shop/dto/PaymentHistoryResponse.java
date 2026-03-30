package com.yeji.domain.shop.dto;

import com.yeji.domain.shop.entity.Payment;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
public class PaymentHistoryResponse {
    private final String orderId;
    private final String productName;
    private final Integer amount;
    private final String status;
    private final LocalDateTime createdAt;

    public PaymentHistoryResponse(Payment payment) {
        this.orderId = payment.getOrderId();
        this.productName = payment.getProduct().getName();
        this.amount = payment.getAmount();
        this.status = payment.getStatus();
        this.createdAt = payment.getCreatedAt();
    }
}