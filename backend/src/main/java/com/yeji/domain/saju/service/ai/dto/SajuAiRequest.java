package com.yeji.domain.saju.service.ai.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

// AI에게 요청 날릴 때 필요한 최소 정보들
// requestId, userContext, inputData (사주 기본 정보)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SajuAiRequest(
        @JsonProperty("request_id")
        String requestId,

        @JsonProperty("user_context")
        UserContext userContext,

        @JsonProperty("input_data")
        JsonNode inputData
) {
    public record UserContext(
            @JsonProperty("user_id") Long userId,
            @JsonProperty("locale") String locale,
            @JsonProperty("timezone") String timezone
    ) {}

    public static SajuAiRequest of(
            String requestId,
            Long userId,
            String locale,
            String timezone,
            JsonNode inputData
    ) {
        return new SajuAiRequest(
                requestId,
                new UserContext(userId, locale, timezone),
                inputData
        );
    }
}
