package com.yeji.domain.unse.service.ai.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AiGreetingRequest(
        @JsonProperty("birth_date") String birthDate,
        @JsonProperty("birth_time") String birthTime, // "HH:mm"
        @JsonProperty("category") String category,
        @JsonProperty("char1_code") String char1Code,
        @JsonProperty("char2_code") String char2Code
) {}
