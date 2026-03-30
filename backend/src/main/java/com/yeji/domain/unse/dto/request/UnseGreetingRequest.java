package com.yeji.domain.unse.dto.request;

import jakarta.validation.constraints.NotBlank;

public record UnseGreetingRequest(
        @NotBlank String session_id,
        @NotBlank String category,
        @NotBlank String char1_code,
        @NotBlank String char2_code
) {}
