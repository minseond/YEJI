package com.yeji.domain.session.model;

import lombok.Getter;
import lombok.Setter;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;

@Getter
public class UserSession {

    private final String sessionId; // 백엔드 세션: sess_xxx
    private final Long userId;

    @Setter
    private SessionPhase phase;

    private final AtomicInteger turnCount = new AtomicInteger(0);
    private final AtomicInteger questionCount = new AtomicInteger(0);

    @Setter
    private Long resultId;

    // ===== UNSE 스냅샷 =====
    @Setter private String unseCategory;          // LOVE / GENERAL ...
    @Setter private Boolean unseForceRegenerate;  // 12시간 내 재생성

    // 회원가입 정보(또는 saju_results 스냅샷 기반)
    @Setter private String birthDate;             // yyyy-MM-dd
    @Setter private String birthTime;             // HH:mm

    // 캐릭터 기본값
    @Setter private String char1Code;             // SOISEOL
    @Setter private String char2Code;             // STELLA

    private final Instant createdAt = Instant.now();

    // ===== AI 세션: AI가 내려준 session_id (예: e826b806) =====
    @Setter
    private String aiSessionId;

    /**
     * aiSessionId가 언제 바인딩되었는지(재호출 방지/만료 판단용).
     */
    @Setter
    private Instant aiSessionBoundAt;

    /**
     * 마지막 greeting 응답(JSON 문자열) 캐시
     * - /unse/prompt 가 "의도치 않게" 재호출되었을 때,
     *   AI 세션을 새로 만들지 않고 기존 greeting 그대로 반환하기 위함.
     */
    @Setter
    private String lastGreetingJson;

    /**
     * greeting 당시의 카테고리(대문자) 캐시 (디버깅/검증용)
     */
    @Setter
    private String lastGreetingCategoryUpper;

    public UserSession(String sessionId, Long userId) {
        this.sessionId = sessionId;
        this.userId = userId;
        this.phase = SessionPhase.SERVICE_SELECT;

        this.unseForceRegenerate = false;
        this.char1Code = "SOISEOL";
        this.char2Code = "STELLA";
    }

    public int getTurnCount() { return turnCount.get(); }
    public int incTurnCount() { return turnCount.incrementAndGet(); }

    public int getQuestionCount() { return questionCount.get(); }
    public int incQuestionCount() { return questionCount.incrementAndGet(); }
}
