package com.yeji.domain.saju.service.ai.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record WesternFortuneAiRequest(
        @JsonProperty("birth_date") String birthDate,
        @JsonProperty("birth_time") String birthTime,
        @JsonProperty("birth_place") String birthPlace,
        @JsonProperty("latitude") Double latitude,
        @JsonProperty("longitude") Double longitude
) {
    public static WesternFortuneAiRequest of(String birthDate,
                                             String birthTime,
                                             String birthPlace,
                                             Double latitude,
                                             Double longitude) {
        return new WesternFortuneAiRequest(birthDate, birthTime, birthPlace, latitude, longitude);
    }
}
