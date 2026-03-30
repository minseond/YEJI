package com.yeji.domain.unse.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
@Profile("test")
@Primary
@RequiredArgsConstructor
public class StubUnseAiClient implements UnseAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public JsonNode greeting(String birthDate, String birthTime, String category, String char1Code, String char2Code) {

        Map<String, Object> res = new LinkedHashMap<>();
        res.put("session_id", "stub_session_001");
        res.put("category", category);

        res.put("messages", List.of(
                msg(char1Code, "GREETING", "(stub) 안녕하세요. 운세 그리팅입니다."),
                msg(char2Code, "GREETING", "(stub) 서양 관점에서 인사를 드립니다."),
                msg(char1Code, "QUESTION", "(stub) 어떤 점이 궁금하신가요?")
        ));

        res.put("turn", 1);
        res.put("suggested_question", "가장 궁금한 점이 있으신가요? (Stub)");
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
                "character", char1Code,
                "type", "ANSWER",
                "content", "(stub) 질문 응답: " + message,
                "timestamp", LocalDateTime.now().toString()
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
        fortune.put("character", "SOISEOL");
        fortune.put("score", 85);
        fortune.put("one_line", "목(木) 기운이 강해 재물 운이 상승하는 시기예요 (Stub)");

        var keywords = fortune.putArray("keywords");
        keywords.add("재물운 상승");
        keywords.add("투자 적기");
        keywords.add("절약 필요");

        fortune.put("detail", "일간(甲)을 중심으로 재성이 왕성하여...");

        return objectMapper.valueToTree(res);
    }

    @Override
    public JsonNode getAnalysis(String fortuneId, String type, String category, String persona, boolean force) {
        ObjectNode res = objectMapper.createObjectNode();
        res.put("fortune_id", fortuneId);
        res.put("fortune_type", type);
        res.put("category", category);
        res.put("score", "85");
        res.put("keyword", "길운이 함께하는 날 (Stub)");

        var details = res.putArray("details");
        ObjectNode detail1 = objectMapper.createObjectNode();
        detail1.put("section", "overall");
        detail1.put("title", "종합 운세");
        detail1.put("description", "오늘은 전반적으로 좋은 기운이 흐르는 날입니다. (Stub)");
        detail1.put("section_code", "OVERALL");
        details.add(detail1);

        res.put("cache_source", "stub");
        return res;
    }

    private Map<String, Object> msg(String character, String type, String content) {
        return Map.of(
                "character", character == null ? "SOISEOL" : character,
                "type", type,
                "content", content,
                "timestamp", LocalDateTime.now().toString()
        );
    }
}
