package com.yeji.domain.unse.dto.request;

import jakarta.validation.constraints.NotBlank;

public record UnseChatTurnRequest(
        @NotBlank String session_id,
        @NotBlank String message
) {}
