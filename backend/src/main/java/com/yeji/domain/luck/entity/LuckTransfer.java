package com.yeji.domain.luck.entity;

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
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
@Table(name = "luck_transfers")
public class LuckTransfer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sender_id", nullable = false)
    private User sender;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "receiver_id", nullable = false)
    private User receiver;

    @Column(name = "transfer_type", nullable = false, length = 20)
    private String transferType; // CURSE, BLESS

    @Column(name = "origin_result_id")
    private Long originResultId;

    @Column(name = "origin_table_type", length = 20)
    private String originTableType;

    @Column(name = "character_type", nullable = false)
    private int characterType = 1;

    @Column(name = "message", columnDefinition = "TEXT")
    private String message;

    @Column(name = "is_read")
    private boolean isRead = false;

    @CreatedDate
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Builder
    public LuckTransfer(User sender, User receiver, String transferType, Long originResultId,
                        String originTableType, int characterType, String message) {
        this.sender = sender;
        this.receiver = receiver;
        this.transferType = transferType;
        this.originResultId = originResultId;
        this.originTableType = originTableType;
        this.characterType = characterType;
        this.message = message;
    }

    public void markAsRead() {
        this.isRead = true;
    }
}