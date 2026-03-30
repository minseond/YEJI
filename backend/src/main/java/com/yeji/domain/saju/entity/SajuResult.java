package com.yeji.domain.saju.entity;

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
@Table(
        name = "saju_results",
        uniqueConstraints = {
                @UniqueConstraint(name = "uq_saju_results_user", columnNames = {"user_id"})
        }
)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class SajuResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    //user_id FK (유저당 1개 결과로 고정)
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    //jsonb 매핑 (사용자 입력값)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "input_data", columnDefinition = "jsonb")
    private JsonNode inputData;

    //jsonb 매핑 (AI 분석 결과)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "analysis_result", columnDefinition = "jsonb")
    private JsonNode analysisResult;

    //점수(저주/축복 기준)
    @Column(name = "score", nullable = false)
    private Integer score;

    //상태 (KEEP, SOLD, SHARED)
    @Column(name = "status", nullable = false, length = 20)
    private String status;

    //생성일
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    //기본값 설정
    @PrePersist
    public void prePersist() {
        LocalDateTime now = LocalDateTime.now(); //현재 기준
        if (this.createdAt == null) this.createdAt = now;
        if (this.updatedAt == null) this.updatedAt = now;

        if (this.status == null || this.status.isBlank()) this.status = "KEEP";
        if (this.score == null) this.score = 0;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
        if (this.status == null || this.status.isBlank()) this.status = "KEEP";
        if (this.score == null) this.score = 0;
    }

    public void overwrite(JsonNode inputData, JsonNode analysisResult) {
        this.inputData = inputData;
        this.analysisResult = analysisResult;
        //업데이트 하면 덮어쓰기 -> 사주 결과 2개 나올 수 없으니까
        if (this.status == null || this.status.isBlank()) this.status = "KEEP";
        if (this.score == null) this.score = 0;
        this.updatedAt = LocalDateTime.now(); //수정일 현재로 업데이트
    }

    @Builder
    public SajuResult(User user,
                      JsonNode inputData,
                      JsonNode analysisResult,
                      Integer score,
                      String status) {
        this.user = user;
        this.inputData = inputData;
        this.analysisResult = analysisResult;
        this.score = (score == null ? 0 : score);
        this.status = (status == null || status.isBlank()) ? "KEEP" : status;

        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }
}
