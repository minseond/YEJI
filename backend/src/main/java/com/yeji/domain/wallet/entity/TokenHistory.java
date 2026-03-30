package com.yeji.domain.wallet.entity;

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
@Table(name = "token_history")
@EntityListeners(AuditingEntityListener.class)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TokenHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "service_code")
    private String serviceCode;

    @Column(name = "amount", nullable = false)
    private Integer amount;

    // CHARGE(충전), USE(사용), REWARD(보상) 등
    @Column(name = "type", length = 30)
    private String type;

    @Column(name = "description")
    private String description;

    @Column(name = "reference_id", length = 100)
    private String referenceId;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Builder
    public TokenHistory(Long userId, String serviceCode, Integer amount, String type, String description, String referenceId) {
        this.userId = userId;
        this.serviceCode = serviceCode;
        this.amount = amount;
        this.type = type;
        this.description = description;
        this.referenceId = referenceId;
    }
}