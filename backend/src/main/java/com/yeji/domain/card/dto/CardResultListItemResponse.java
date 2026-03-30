package com.yeji.domain.card.dto;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.card.entity.CardResult;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
public class CardResultListItemResponse {

    private final Long cardResultId;
    private final String category;
    private final String question;

    private final Integer score;
    private final String status;

    private final LocalDateTime createdAt;
    private final String summary;

    public CardResultListItemResponse(CardResult result) {
        this.cardResultId = result.getId();
        this.category = result.getCategory().name();
        this.question = result.getQuestion();

        this.score = result.getScore();
        this.status = result.getStatus().name();

        this.createdAt = result.getCreatedAt();
        this.summary = summarize(result.getAiReading());
    }

    private String summarize(String aiReading) {
        if (aiReading == null) return null;
        try {
            ObjectMapper om = new ObjectMapper();
            JsonNode root = om.readTree(aiReading);
            JsonNode data = root.has("data") ? root.get("data") : root;

            // 1) data.summary.overall_theme
            JsonNode summary = data.path("summary");
            if (summary.isObject() && summary.hasNonNull("overall_theme")) {
                return clip(summary.get("overall_theme").asText());
            }

            // 2) data.summary.advice
            if (summary.isObject() && summary.hasNonNull("advice")) {
                return clip(summary.get("advice").asText());
            }

            // 3) 첫 카드 interpretation
            JsonNode cards = data.path("cards");
            if (cards.isArray() && cards.size() > 0) {
                JsonNode first = cards.get(0);
                if (first.hasNonNull("interpretation")) {
                    return clip(first.get("interpretation").asText());
                }
            }

            // 4) fallback message
            if (data.hasNonNull("message")) {
                return clip(data.get("message").asText());
            }
        } catch (Exception ignore) {
            // ignore
        }

        // JSON 파싱 실패 시: 그냥 앞부분만
        String oneLine = aiReading.replaceAll("\\s+", " ").trim();
        if (oneLine.isBlank()) return null;
        return clip(oneLine);
    }

    private String clip(String s) {
        if (s == null) return null;
        String oneLine = s.replaceAll("\\s+", " ").trim();
        if (oneLine.isBlank()) return null;
        int limit = 60;
        return oneLine.length() <= limit ? oneLine : oneLine.substring(0, limit) + "...";
    }
}
