package com.yeji.domain.saju.service.ai.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record EasternFortuneAiRequest(
        @JsonProperty("birth_date") String birthDate,
        @JsonProperty("birth_time") String birthTime,
        @JsonProperty("gender") String gender,
        @JsonProperty("name") String name
) {
    public static EasternFortuneAiRequest of(String birthDate, String birthTime, String gender, String name) {
        return new EasternFortuneAiRequest(birthDate, birthTime, gender, name);
    }
}
