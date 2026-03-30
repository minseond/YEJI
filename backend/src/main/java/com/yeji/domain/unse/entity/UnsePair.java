package com.yeji.domain.unse.entity;

import com.fasterxml.jackson.databind.JsonNode;
import com.yeji.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;

@Entity
@Getter
@Table(name = "unse_pairs")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UnsePair {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    // user_id FK
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 카테고리 (예: STUDY)
    @Column(name = "category", nullable = false, length = 30)
    private String category;

    // 동양 결과 JSON (필수)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "eastern", nullable = false, columnDefinition = "jsonb")
    private JsonNode eastern;

    // 서양 결과 JSON (필수)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "western", nullable = false, columnDefinition = "jsonb")
    private JsonNode western;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (this.createdAt == null) this.createdAt = LocalDateTime.now();
    }

    /**
     * 동/서양 결과 갱신 (JPA dirty checking)
     */
    public void updateEastern(JsonNode eastern) {
        this.eastern = eastern;
    }

    public void updateWestern(JsonNode western) {
        this.western = western;
    }

    @Builder
    public UnsePair(User user,
                    String category,
                    JsonNode eastern,
                    JsonNode western) {
        this.user = user;
        this.category = category;
        this.eastern = eastern;
        this.western = western;
        this.createdAt = LocalDateTime.now();
    }
}
