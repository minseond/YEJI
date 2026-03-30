package com.yeji.domain.compatibility.entity;

import com.yeji.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
@Table(name = "compatibility_results")
public class CompatibilityResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "req_id", nullable = false)
    private User requester;

    @Column(name = "target_id")
    private Long targetId;

    @Column(name = "target_name", length = 50)
    private String targetName;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "target_birth_data", columnDefinition = "jsonb")
    private Map<String, Object> targetBirthData;

    @Column(name = "relation_type", length = 50)
    private String relationType;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "result_data", columnDefinition = "jsonb")
    private Map<String, Object> resultData;

    @CreatedDate
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Builder
    public CompatibilityResult(User requester, Long targetId, String targetName,
                               Map<String, Object> targetBirthData, String relationType,
                               Map<String, Object> resultData) {
        this.requester = requester;
        this.targetId = targetId;
        this.targetName = targetName;
        this.targetBirthData = targetBirthData;
        this.relationType = relationType;
        this.resultData = resultData;
    }
}