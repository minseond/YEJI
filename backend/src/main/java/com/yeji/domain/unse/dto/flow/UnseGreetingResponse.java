package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * AI Swagger: POST /v1/fortune/chat/greeting 응답 스키마
 * - 프론트가 그대로 쓰도록 필드를 최대한 동일하게 맞춥니다.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record UnseGreetingResponse(
        @JsonProperty("session_id")
        String sessionId,

        @JsonProperty("turn")
        Integer turn,

        List<Message> messages,

        @JsonProperty("suggested_question")
        String suggestedQuestion,

        @JsonProperty("is_complete")
        Boolean isComplete
) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Message(
            String character,
            String type,
            String content,
            /**
             * AI는 문자열(datetime)로 내려주므로 String으로 받는 게 안전합니다.
             * 예: "2026-02-01T17:36:44.739261"
             */
            String timestamp
    ) {}
}
