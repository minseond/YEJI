package com.yeji.domain.saju.service.ai.validation;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * AI 응답 최소 검증
 */
@Slf4j
@Component
public class FortuneV2ResponseValidator {

    public static void validateOrThrow(JsonNode root) {
        if (root == null || root.isNull()) {
            throw new IllegalStateException("AI 응답이 비어 있습니다.");
        }

        JsonNode eastern = root.get("eastern");
        if (eastern == null || eastern.isNull()) {
            throw new IllegalStateException("AI 응답 eastern 블록이 없습니다.");
        }

        String easternSummary = findEasternSummary(eastern);
        if (easternSummary == null || easternSummary.isBlank()) {
            log.warn("[Saju AI] eastern summary missing. raw={}", eastern.toString());
            throw new IllegalStateException("AI 응답 eastern 요약 텍스트를 찾지 못했습니다.");
        }

        JsonNode western = root.get("western");
        if (western == null || western.isNull()) {
            throw new IllegalStateException("AI 응답 western 블록이 없습니다.");
        }
    }

    private static String findEasternSummary(JsonNode eastern) {
        JsonNode n1 = eastern.at("/data/chart/summary");
        if (n1.isTextual()) return n1.asText();

        JsonNode n2 = eastern.at("/chart/summary");
        if (n2.isTextual()) return n2.asText();

        JsonNode n3 = eastern.get("summary");
        if (n3 != null && n3.isTextual()) return n3.asText();

        return null;
    }

    private static String firstNonBlankTextByPaths(JsonNode node, List<String> paths) {
        if (node == null || node.isNull()) return null;
        for (String p : paths) {
            JsonNode target = node;
            String[] parts = p.split("\\.");
            for (String part : parts) {
                target = target.get(part);
                if (target == null || target.isNull()) break;
            }
            if (target != null && target.isTextual() && !target.asText().isBlank()) {
                return target.asText();
            }
        }
        return null;
    }
}
