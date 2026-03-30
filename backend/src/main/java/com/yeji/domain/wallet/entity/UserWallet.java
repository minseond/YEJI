package com.yeji.domain.wallet.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.UpdateTimestamp;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Getter
@Table(name = "user_wallet")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
public class UserWallet {

    @Id
    @Column(name = "user_id")
    private Long userId;

    @Column(name = "balance", nullable = false)
    private Integer balance;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    public UserWallet(Long userId) {
        this.userId = userId;
        this.balance = 0;
    }

    // 잔액 변경 (비즈니스 로직)
    public void addBalance(int amount) {
        this.balance += amount;
    }

    public void subtractBalance(int amount) {
        if (this.balance < amount) {
            throw new RuntimeException("잔액이 부족합니다.");
        }
        this.balance -= amount;
    }
}