package com.yeji.domain.card.entity;

import com.yeji.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Getter
@Table(name = "card_results")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class CardResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "category", nullable = false, length = 20)
    private CardCategory category;

    @Column(name = "question", columnDefinition = "text")
    private String question;

    @Column(name = "ai_reading", columnDefinition = "jsonb")
    private String aiReading;

    @Column(name = "score", nullable = false)
    private Integer score;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private CardStatus status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (this.createdAt == null) this.createdAt = LocalDateTime.now();
        if (this.category == null) this.category = CardCategory.TARO;
        if (this.score == null) this.score = 0;
        if (this.status == null) this.status = CardStatus.KEEP;
    }

    @Builder
    public CardResult(User user,
                      CardCategory category,
                      String question,
                      String aiReading,
                      Integer score,
                      CardStatus status) {
        this.user = user;
        this.category = (category == null) ? CardCategory.TARO : category;
        this.question = question;
        this.aiReading = aiReading;
        this.score = (score == null) ? 0 : score;
        this.status = (status == null) ? CardStatus.KEEP : status;
    }

    public void updateAiReading(String aiReading) {
        this.aiReading = aiReading;
    }

    public void updateStatus(CardStatus status) {
        if (status != null) this.status = status;
    }

    public void updateScore(Integer score) {
        if (score != null) this.score = score;
    }
}
