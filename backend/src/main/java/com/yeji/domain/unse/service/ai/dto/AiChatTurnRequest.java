package com.yeji.domain.unse.service.ai.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AiChatTurnRequest(
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("message") String message,
        @JsonProperty("char1_code") String char1Code,
        @JsonProperty("char2_code") String char2Code,
        @JsonProperty("extend_turn") boolean extendTurn
) {}
