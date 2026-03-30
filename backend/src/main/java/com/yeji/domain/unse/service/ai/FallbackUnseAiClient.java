package com.yeji.domain.unse.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class FallbackUnseAiClient implements UnseAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public JsonNode greeting(String birthDate, String birthTime, String category, String char1Code, String char2Code) {

        String sid = "fallback_" + UUID.randomUUID().toString().substring(0, 8);

        Map<String, Object> res = new LinkedHashMap<>();
        res.put("session_id", sid);
        res.put("category", category);

        res.put("messages", List.of(
                msg(char1Code, "GREETING", "현재 AI 서버가 불안정합니다."),
                msg(char2Code, "QUESTION", "잠시 후 다시 시도해 주세요.")
        ));

        res.put("turn", 1);
        res.put("suggested_question", "잠시 후 다시 시도해 주세요.");
        res.put("is_complete", false);

        return objectMapper.valueToTree(res);
    }

    @Override
    public Flux<JsonNode> streamChatTurn(
            String aiSessionId,
            String message,
            String char1Code,
            String char2Code,
            boolean extendTurn
    ) {
        JsonNode ev = objectMapper.valueToTree(Map.of(
                "character", "SYSTEM",
                "type", "ERROR",
                "content", "AI 서버 장애로 응답을 생성할 수 없습니다.",
                "timestamp", Instant.now().toString()
        ));
        return Flux.just(ev);
    }

    @Override
    public JsonNode getChatSummary(String aiSessionId, String type, String category) {
        ObjectNode res = objectMapper.createObjectNode();
        res.put("session_id", aiSessionId);
        res.put("category", category);
        res.put("fortune_type", type);

        ObjectNode fortune = res.putObject("fortune");
        fortune.put("character", "SYSTEM");
        fortune.put("score", 50);
        fortune.put("one_line", "일시적인 오류로 운세 요약을 불러올 수 없습니다.");

        var keywords = fortune.putArray("keywords");
        keywords.add("데이터 없음");

        fortune.put("detail", "잠시 후 다시 시도해 주세요.");

        res.put("model", "fallback-unse");
        res.put("generated_at", Instant.now().toString());

        return objectMapper.valueToTree(res);
    }

    @Override
    public JsonNode getAnalysis(String fortuneId, String type, String category, String persona, boolean force) {
        ObjectNode res = objectMapper.createObjectNode();
        res.put("fortune_id", fortuneId);
        res.put("fortune_type", type);
        res.put("category", category);
        res.put("score", "50");
        res.put("keyword", "연결 실패");
        res.putArray("details");
        res.put("cache_source", "none");
        return res;
    }

    private Map<String, Object> msg(String character, String type, String content) {
        return Map.of(
                "character", character == null ? "SOISEOL" : character,
                "type", type,
                "content", content,
                "timestamp", Instant.now().toString()
        );
    }
}
