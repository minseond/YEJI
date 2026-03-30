package com.yeji.domain.saju.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

import java.time.OffsetDateTime;

//AI 결과를 JSON으로 다 받아오기
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SajuAnalyzeResponse(
        boolean success,
        Meta meta,
        @JsonProperty("analysis_result")
        JsonNode analysisResult
) {
    public record Meta(
            @JsonProperty("result_id") Long resultId,
            @JsonProperty("generated_at") OffsetDateTime generatedAt,
            String source
    ) {}

    public static SajuAnalyzeResponse ok(Long resultId, OffsetDateTime generatedAt, String source, JsonNode analysisResult) {
        return new SajuAnalyzeResponse(true, new Meta(resultId, generatedAt, source), analysisResult);
    }
}
