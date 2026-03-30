package com.yeji.domain.saju.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.NoArgsConstructor;

// Front -> Back (요청 DTO)
@Getter
@NoArgsConstructor
@Schema(description = "사주 분석 요청 DTO")
public class SajuAnalyzeRequest {

    //input_data 에 사용자 정보 넣어서 요청
    @JsonProperty("input_data")
    private JsonNode inputData;
}
