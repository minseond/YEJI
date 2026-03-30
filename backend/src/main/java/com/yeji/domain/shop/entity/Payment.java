package com.yeji.domain.shop.entity;

import com.yeji.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Getter
@Table(name = "payments")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
public class Payment {

    @Id
    @Column(name = "order_id", length = 100)
    private String orderId; // UUID 등 고유 주문 번호

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    @Column(name = "amount")
    private Integer amount; // 실제 결제 금액 (KRW)

    @Column(name = "pg_provider", length = 50)
    private String pgProvider; // kakaopay, toss 등

    // PENDING(대기), PAID(완료), FAILED(실패), CANCELLED(취소)
    @Column(name = "status", length = 20)
    private String status;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Builder
    public Payment(String orderId, User user, Product product, Integer amount, String pgProvider, String status) {
        this.orderId = orderId;
        this.user = user;
        this.product = product;
        this.amount = amount;
        this.pgProvider = pgProvider;
        this.status = status;
    }

    public void complete(String pgProvider) {
        this.status = "PAID";
        this.pgProvider = pgProvider;
    }

    public void fail() {
        this.status = "FAILED";
    }
}