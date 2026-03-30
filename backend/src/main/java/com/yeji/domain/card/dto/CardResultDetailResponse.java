package com.yeji.domain.card.dto;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.card.entity.CardResult;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
public class CardResultDetailResponse {

    private final Long cardResultId;
    private final Long userId;
    private final String category;
    private final String question;

    /**
     * AI 원본 응답 JSON (프론트에서 data.cards, data.summary 등을 바로 꺼낼 수 있게)
     */
    private final JsonNode aiReading;

    private final Integer score;
    private final String status;

    private final LocalDateTime createdAt;
    private final List<CardSelectedCardResponse> cards;

    private CardResultDetailResponse(
            Long cardResultId,
            Long userId,
            String category,
            String question,
            JsonNode aiReading,
            Integer score,
            String status,
            LocalDateTime createdAt,
            List<CardSelectedCardResponse> cards
    ) {
        this.cardResultId = cardResultId;
        this.userId = userId;
        this.category = category;
        this.question = question;
        this.aiReading = aiReading;
        this.score = score;
        this.status = status;
        this.createdAt = createdAt;
        this.cards = cards;
    }

    public static CardResultDetailResponse of(CardResult result, List<CardSelectedCardResponse> cards, ObjectMapper objectMapper) {
        JsonNode ai = parseAiReading(result.getAiReading(), objectMapper);

        return new CardResultDetailResponse(
                result.getId(),
                result.getUser().getId(),
                result.getCategory().name(),
                result.getQuestion(),
                ai,
                result.getScore(),
                result.getStatus().name(),
                result.getCreatedAt(),
                cards
        );
    }

    private static JsonNode parseAiReading(String aiReadingJson, ObjectMapper objectMapper) {
        if (aiReadingJson == null || aiReadingJson.isBlank()) {
            ObjectNode empty = objectMapper.createObjectNode();
            empty.put("success", true);
            empty.put("validated", false);
            empty.put("type", "empty");
            empty.putObject("data").put("message", "aiReading is empty");
            empty.putNull("errors");
            empty.put("latency_ms", 0);
            return empty;
        }

        try {
            return objectMapper.readTree(aiReadingJson);
        } catch (Exception e) {
            // 예전 데이터가 문자열로 들어간 경우 대비
            ObjectNode wrapped = objectMapper.createObjectNode();
            wrapped.put("success", true);
            wrapped.put("validated", false);
            wrapped.put("type", "raw-wrapped");
            wrapped.putObject("data").put("raw", aiReadingJson);
            wrapped.putNull("errors");
            wrapped.put("latency_ms", 0);
            return wrapped;
        }
    }
}
