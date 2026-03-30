package com.yeji.domain.unse.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.time.OffsetDateTime;
import java.time.ZoneId;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnseFinalResponse(
        @JsonProperty("result_id") Long resultId,
        String category,
        @JsonProperty("analysis_result") JsonNode analysisResult,
        @JsonProperty("generated_at") OffsetDateTime generatedAt
) {
    private static final ZoneId KST = ZoneId.of("Asia/Seoul");

    public static UnseFinalResponse from(Long resultId, String category, JsonNode analysisResult) {
        if (analysisResult == null || analysisResult.isNull()) {
            throw new IllegalArgumentException("analysisResult is null");
        }
        return new UnseFinalResponse(resultId, category, analysisResult, OffsetDateTime.now(KST));
    }
}
