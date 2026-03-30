package com.yeji.domain.saju.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.saju.service.ai.dto.SajuAiRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Real AI client for Saju (Eastern/Western)
 */
@Slf4j
@Primary
@Component
@RequiredArgsConstructor
@Profile({"dev", "prod", "local"})
public class RealSajuAiClient implements SajuAiClient {

    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    @Value("${ai.yeji.base-url}")
    private String baseUrl;

    @Value("${ai.yeji.fortune.eastern-endpoint}")
    private String easternEndpoint;

    @Value("${ai.yeji.fortune.western-endpoint}")
    private String westernEndpoint;

    @Value("${ai.yeji.fortune.timeout-ms:600000}")
    private long timeoutMs;

    @Override
    public JsonNode analyze(SajuAiRequest request) {
        WebClient client = webClient.mutate()
                .baseUrl(baseUrl)
                .build();

        JsonNode input = request.inputData();
        if (input == null || input.isNull()) {
            throw new IllegalArgumentException("input_data is empty");
        }

        String birthDate  = textOrNull(input.get("birth_date"));
        String birthTime  = textOrNull(input.get("birth_time"));
        String gender     = textOrNull(input.get("gender"));
        String name       = textOrNull(input.get("name_kor"));
        String birthPlace = textOrNull(input.get("birth_place"));
        Double latitude   = doubleOrNull(input.get("latitude"));
        Double longitude  = doubleOrNull(input.get("longitude"));

        if (birthDate == null || birthDate.isBlank()) {
            throw new IllegalArgumentException("birth_date is required (YYYY-MM-DD)");
        }

        // Default Location
        if (birthPlace == null || birthPlace.isBlank()) birthPlace = "Seoul, Korea";
        if (latitude == null) latitude = 37.5665;
        if (longitude == null) longitude = 126.9780;

        // Eastern Body
        ObjectNode eastBody = objectMapper.createObjectNode();
        eastBody.put("birth_date", birthDate);
        if (birthTime != null) eastBody.put("birth_time", birthTime);
        if (gender != null) eastBody.put("gender", gender);
        if (name != null) eastBody.put("name", name);

        // Western Body
        ObjectNode westBody = objectMapper.createObjectNode();
        westBody.put("birth_date", birthDate);
        if (birthTime != null) westBody.put("birth_time", birthTime);
        westBody.put("birth_place", birthPlace);
        westBody.put("latitude", latitude);
        westBody.put("longitude", longitude);
        if (gender != null) westBody.put("gender", gender);
        if (name != null) westBody.put("name", name);

        Duration timeout = Duration.ofMillis(timeoutMs);
        String query = "?skip_validation=false&graceful=true";

        Mono<JsonNode> eastMono = postAndParseOrSalvage(client, easternEndpoint + query, eastBody, "eastern")
                .timeout(timeout);

        Mono<JsonNode> westMono = postAndParseOrSalvage(client, westernEndpoint + query, westBody, "western")
                .timeout(timeout);

        JsonNode result = Mono.zip(eastMono, westMono)
                .map(tuple -> {
                    JsonNode eastNode = ensureEasternSchema(tuple.getT1());
                    JsonNode westNode = ensureWesternSchema(tuple.getT2());

                    Map<String, Object> merged = new LinkedHashMap<>();
                    merged.put("eastern", eastNode);
                    merged.put("western", westNode);
                    return (JsonNode) objectMapper.valueToTree(merged);
                })
                .block(timeout);

        return result;
    }

    private Mono<JsonNode> postAndParseOrSalvage(WebClient client, String endpoint, ObjectNode body, String label) {
        return client.post()
                .uri(endpoint)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .exchangeToMono(res -> {
                    if (res.statusCode().is2xxSuccessful()) {
                        return res.bodyToMono(JsonNode.class);
                    }

                    return res.bodyToMono(String.class)
                            .defaultIfEmpty("")
                            .flatMap(errorBody -> {
                                JsonNode salvaged = extractAndFixRawContent(errorBody, label);
                                if (salvaged != null) {
                                    log.info("[AI {} SALVAGED] status={}", label.toUpperCase(), res.statusCode());
                                    return Mono.just(salvaged);
                                }
                                return Mono.error(new RuntimeException("AI " + label + " Failed (" + res.statusCode() + ")"));
                            });
                });
    }

    private JsonNode extractAndFixRawContent(String errorBody, String label) {
        if (errorBody == null || errorBody.isBlank()) return null;
        try {
            JsonNode root = objectMapper.readTree(errorBody);
            JsonNode detail = root.get("detail");
            if (detail == null || detail.isNull()) return null;

            JsonNode raw = detail.get("raw_content");
            if (raw == null || raw.isNull() || !raw.isTextual()) return null;

            JsonNode parsed = objectMapper.readTree(raw.asText());
            if ("western".equalsIgnoreCase(label) && parsed != null && parsed.isObject()) {
                fixWesternKeywords((ObjectNode) parsed);
            }
            return parsed;
        } catch (Exception e) {
            return null;
        }
    }

    private void fixWesternKeywords(ObjectNode westernObj) {
        JsonNode statsNode = westernObj.get("stats");
        if (statsNode != null && statsNode.isObject()) {
            ObjectNode statsObj = (ObjectNode) statsNode;
            JsonNode keywordsNode = statsObj.get("keywords");
            if (keywordsNode == null || keywordsNode.isNull() || !keywordsNode.isArray()) {
                ArrayNode keywordsArr = objectMapper.createArrayNode();
                JsonNode summaryNode = statsObj.get("keywords_summary");
                if (summaryNode != null && summaryNode.isTextual()) {
                    String[] parts = summaryNode.asText().split(",");
                    for (String p : parts) {
                        String s = p.trim();
                        if (!s.isEmpty()) keywordsArr.add(s);
                    }
                }
                statsObj.set("keywords", keywordsArr);
            }
        }
    }

    private JsonNode ensureEasternSchema(JsonNode node) {
        node = unwrapData(node);
        ObjectNode obj = (node != null && node.isObject()) ? (ObjectNode) node : objectMapper.createObjectNode();
        JsonNode chart = obj.get("chart");
        if (chart == null || chart.isNull() || !chart.isObject()) {
            ObjectNode newChart = objectMapper.createObjectNode();
            newChart.put("summary", "사주 요약 정보를 불러올 수 없습니다.");
            obj.set("chart", newChart);
        }
        return obj;
    }

    private JsonNode ensureWesternSchema(JsonNode node) {
        node = unwrapData(node);
        ObjectNode obj = (node != null && node.isObject()) ? (ObjectNode) node : objectMapper.createObjectNode();
        JsonNode stats = obj.get("stats");
        if (stats == null || stats.isNull() || !stats.isObject()) {
            ObjectNode newStats = objectMapper.createObjectNode();
            ObjectNode mainSign = objectMapper.createObjectNode();
            mainSign.put("name", "별자리");
            newStats.set("main_sign", mainSign);
            obj.set("stats", newStats);
        }
        return obj;
    }

    private JsonNode unwrapData(JsonNode node) {
        if (node != null && node.isObject() && node.has("data") && node.get("data").isObject()) {
            return node.get("data");
        }
        return node;
    }

    private String textOrNull(JsonNode node) {
        return (node == null || node.isNull()) ? null : node.asText();
    }

    private Double doubleOrNull(JsonNode node) {
        if (node == null || node.isNull()) return null;
        if (node.isNumber()) return node.asDouble();
        try { return Double.parseDouble(node.asText()); } catch (Exception e) { return null; }
    }
}