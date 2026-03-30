package com.yeji.domain.unse.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnseAnalyzeResponse(
        @JsonProperty("result_id") Long resultId,
        @JsonProperty("analysis_result") JsonNode analysisResult
) {}
