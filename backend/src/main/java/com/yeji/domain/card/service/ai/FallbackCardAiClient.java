package com.yeji.domain.card.service.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.card.entity.CardCategory;
import com.yeji.domain.card.entity.CardSelection;
import com.yeji.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * AI 서버 장애 시 사용되는 폴백 카드 클라이언트
 * - AI 원본 응답 형태를 최대한 맞춰서 JSON으로 반환
 */
@Component
@RequiredArgsConstructor
public class FallbackCardAiClient implements CardAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public CardAiResult reading(User user, CardCategory category, String question, List<CardSelection> selections) {
        // AI 응답 형태 최대한 맞춰서 AI_READING에 JSON으로 박기
        // 프론트는 aiReading.data.* 를 그대로 꺼내서 사용할 수 있음!
        ObjectNode root = objectMapper.createObjectNode();
        root.put("success", true);
        root.put("validated", false);
        root.put("type", "fallback");

        ObjectNode data = root.putObject("data");
        data.put("category", category == null ? "" : category.name().toLowerCase());
        data.put("question", question == null ? "" : question);
        data.put("message", "현재 AI 서버가 일시적으로 불안정하여 상세 해석을 제공하기 어렵습니다.");
        data.put("selected_cards", selections == null ? 0 : selections.size());

        root.putNull("errors");
        root.put("latency_ms", 0);

        return new CardAiResult(root);
    }
}
