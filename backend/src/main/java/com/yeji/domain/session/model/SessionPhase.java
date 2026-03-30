package com.yeji.domain.session.model;

//세션 단계 정의
public enum SessionPhase {
    SERVICE_SELECT,
    CATEGORY_SELECT,
    ANALYZING,
    RESULT_STREAMING,
    DISCUSSION,
    PAUSED,
    COMPLETE,
    /** 운세 도메인: 프롬프트(카테고리 선택) 완료 + 그리팅 완료 */
    FORTUNE_READY,
    /** 운세 도메인: (대화/요약까지) 플로우 종료 */
    FORTUNE_DONE;

    public String getWriteName() {
        return switch (this) {
            case SERVICE_SELECT -> "service_select";
            case CATEGORY_SELECT -> "category_select";
            case ANALYZING -> "analyzing";
            case RESULT_STREAMING -> "result_streaming";
            case DISCUSSION -> "discussion";
            case PAUSED -> "paused";
            case COMPLETE -> "complete";
            case FORTUNE_READY -> "fortune_ready";
            case FORTUNE_DONE -> "fortune_done";
        };
    }
}
