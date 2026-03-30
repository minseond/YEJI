package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

/**
 * /unse/prompt 요청 DTO
 *
 * AI Swagger(/v1/fortune/chat/greeting) 요청 구조를 최대한 그대로 따르되,
 * 기존 백엔드 플로우(SessionService 기반)를 유지하기 위해 session_id를 optional로 허용합니다.
 *
 * 프론트가 session_id를 보내지 않는다면(=AI 스키마 그대로),
 * 기존 세션 흐름을 위해 다른 방식(예: 세션 생성 API)을 통해 session_id를 확보한 뒤 호출하는 것을 권장합니다.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnseGreetingRequest(
        /** 백엔드 세션ID (기존 로직 호환용, optional) */
        @JsonProperty("session_id") String sessionId,

        @NotBlank @JsonProperty("birth_date") String birthDate,
        @NotBlank @JsonProperty("birth_time") String birthTime,
        @NotBlank String category,
        @NotBlank @JsonProperty("char1_code") String char1Code,
        @NotBlank @JsonProperty("char2_code") String char2Code,

        /** 12시간 이내 재생성 강제(기존 로직 호환용, optional) */
        @JsonProperty("force_regenerate") Boolean forceRegenerate
) {}
