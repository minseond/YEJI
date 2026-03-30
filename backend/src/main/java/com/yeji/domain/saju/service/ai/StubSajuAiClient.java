package com.yeji.domain.saju.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.saju.service.ai.dto.SajuAiRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class StubSajuAiClient implements SajuAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public JsonNode analyze(SajuAiRequest request) {
        // dummyFortuneV2 최소 구조 반환 (프론트 깨짐 방지용)
        // AI 모델 붙으면 여기는 삭제해도 됨
        Map<String, Object> eastern = new LinkedHashMap<>();
        eastern.put("element", "WOOD");
        eastern.put("chart", Map.of("summary", "Stub: eastern.chart.summary"));
        eastern.put("stats", Map.of(
                "five_elements", Map.of("summary", "Stub", "list", List.of())
        ));
        eastern.put("final_verdict", Map.of(
                "summary", "Stub",
                "strength", "",
                "weakness", "",
                "advice", ""
        ));
        eastern.put("lucky", Map.of("color", "", "number", "", "item", ""));

        Map<String, Object> western = new LinkedHashMap<>();
        western.put("element", "WATER");
        western.put("stats", Map.of(
                "main_sign", Map.of("name", "Pisces"),
                "element_summary", "Stub",
                "element_4_distribution", List.of(),
                "modality_summary", "Stub",
                "modality_3_distribution", List.of(),
                "keywords_summary", "Stub",
                "keywords", List.of()
        ));
        western.put("fortune_content", Map.of(
                "overview", "Stub: western.fortune_content.overview",
                "detailed_analysis", List.of(),
                "advice", ""
        ));
        western.put("lucky", Map.of("color", "", "number", "", "item", ""));

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("eastern", eastern);
        root.put("western", western);

        // 디버그용 echo (원하면 제거)
        root.put("_echo", Map.of(
                "request_id", request != null ? request.requestId() : null,
                "user_context", request != null ? request.userContext() : null,
                "input_data", request != null ? request.inputData() : null
        ));

        return objectMapper.valueToTree(root);
    }
}
