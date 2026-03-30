package com.yeji.domain.card.service.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.card.entity.CardCategory;
import com.yeji.domain.card.entity.CardSelection;
import com.yeji.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@RequiredArgsConstructor
@Profile("test")
@Primary
public class StubCardAiClient implements CardAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public CardAiResult reading(User user, CardCategory category, String question, List<CardSelection> selections) {
        int expected = (category == CardCategory.HWATU) ? 4 : 3;

        ObjectNode root = objectMapper.createObjectNode();
        root.put("success", true);
        root.put("validated", true);
        root.put("type", "stub");

        ObjectNode data = root.putObject("data");
        data.put("category", category == null ? "" : category.name().toLowerCase());
        data.put("question", question == null ? "" : question);
        data.put("selected_cards", selections == null ? 0 : selections.size());
        data.put("expected_cards", expected);
        data.put("message", "(stub) 오늘은 '정리'와 '우선순위'가 핵심입니다. 급하게 결론내기보다 선택지를 좁혀가면 좋습니다.");

        root.putNull("errors");
        root.put("latency_ms", 0);

        return new CardAiResult(root);
    }
}
