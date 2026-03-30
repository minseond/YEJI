package com.yeji.domain.saju.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.saju.service.ai.dto.SajuAiRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

//프론트 변경 스키마에 맞춰서 수정함
@Component
@RequiredArgsConstructor
@ConditionalOnMissingBean(SajuAiClient.class)
public class FallbackSajuAiClient implements SajuAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public JsonNode analyze(SajuAiRequest request) {
        Map<String, Object> eastern = new LinkedHashMap<>();
        eastern.put("element", "WOOD");
        eastern.put("chart", Map.of("summary", "Fallback: eastern.chart.summary"));
        eastern.put("stats", Map.of("five_elements", Map.of("summary", "Fallback", "list", List.of())));
        eastern.put("final_verdict", Map.of("summary", "Fallback", "strength", "", "weakness", "", "advice", ""));
        eastern.put("lucky", Map.of("color", "", "number", "", "item", ""));

        Map<String, Object> western = new LinkedHashMap<>();
        western.put("element", "WATER");
        western.put("stats", Map.of(
                "main_sign", Map.of("name", "Pisces"),
                "element_summary", "Fallback",
                "element_4_distribution", List.of(),
                "modality_summary", "Fallback",
                "modality_3_distribution", List.of(),
                "keywords_summary", "Fallback",
                "keywords", List.of()
        ));
        western.put("fortune_content", Map.of(
                "overview", "Fallback: western.fortune_content.overview",
                "detailed_analysis", List.of(),
                "advice", ""
        ));
        western.put("lucky", Map.of("color", "", "number", "", "item", ""));

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("eastern", eastern);
        root.put("western", western);

        return objectMapper.valueToTree(root);
    }
}
