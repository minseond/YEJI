package com.yeji.domain.unse.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public record UnseGenerateRequest(
        @JsonProperty("session_id")
        @NotBlank String sessionId,

        @NotBlank String category,

        @JsonProperty("force_regenerate")
        Boolean forceRegenerate,

        @JsonProperty("char1_code")
        String char1Code,

        @JsonProperty("char2_code")
        String char2Code
) {}
