package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public record UnseChatTurnRequest(
        @JsonProperty("session_id")
        @NotBlank String sessionId,

        @NotBlank String message
) {}
