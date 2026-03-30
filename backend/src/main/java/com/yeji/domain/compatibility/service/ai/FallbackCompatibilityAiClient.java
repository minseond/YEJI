package com.yeji.domain.compatibility.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/**
 * AI 장애/타임아웃 시 반환할 최소 응답.
 * AI Swagger(/v1/fortune/compatibility) 응답 스키마와 동일한 형태 (wrapper 없음)
 */
@Component
@RequiredArgsConstructor
public class FallbackCompatibilityAiClient {

    private final ObjectMapper objectMapper;

    public JsonNode fallback() {
        ObjectNode root = objectMapper.createObjectNode();

        ObjectNode score = root.putObject("score");
        score.put("total", 50);
        score.put("east", 25);
        score.put("west", 25);

        root.put("grade", "normal");
        root.put("grade_label", "무난한 궁합");
        root.put("score_range", "normal");

        ObjectNode message = root.putObject("message");

        ObjectNode east = message.putObject("east");
        ObjectNode eastRel = east.putObject("relationship_dynamics");
        eastRel.putObject("communication").put("desc", "대화는 무난한 편입니다. 핵심 감정은 짧게라도 공유해 보세요.");
        eastRel.putObject("flexibility").put("desc", "상황에 따라 조율할 여지가 있습니다. 작은 타협점을 먼저 정해두면 좋아요.");
        eastRel.putObject("stability").put("desc", "기본적인 안정감은 유지됩니다. 루틴을 맞추면 더 편안해질 수 있어요.");
        eastRel.putObject("passion").put("desc", "열정은 서서히 올라오는 타입입니다. 소소한 이벤트로 분위기를 살려보세요.");
        eastRel.putObject("growth").put("desc", "함께 성장할 가능성이 있습니다. 공동 목표를 작게라도 세워보세요.");

        ObjectNode eastSum = east.putObject("compatibility_summary");
        eastSum.putArray("keywords").add("평온").add("조율");
        eastSum.put("desc", "현재는 무난한 흐름입니다. 대화의 리듬과 역할 분담을 맞추면 관계 만족도가 올라갈 수 있어요.");

        ObjectNode west = message.putObject("west");
        ObjectNode zodiac = west.putObject("zodiac");
        ObjectNode aspects = zodiac.putObject("aspects");
        aspects.putObject("moon_resonance").put("title", "정서적 교감").put("desc", "감정 신호를 알아차리는 연습이 도움이 됩니다.");
        aspects.putObject("mercury_communication").put("title", "의사소통 패턴").put("desc", "사실/감정의 우선순위를 맞추면 오해가 줄어요.");
        aspects.putObject("venus_mars_values").put("title", "애정의 조화").put("desc", "표현 방식의 차이를 존중하면 체감 만족도가 커집니다.");
        aspects.putObject("saturn_stability").put("title", "책임의 무게").put("desc", "작은 규칙 합의가 장기 안정에 도움이 됩니다.");

        ObjectNode numerology = west.putObject("numerology");
        numerology.putObject("life_path").put("title", "인생 여정").put("desc", "큰 방향은 맞출 수 있는 편입니다.");
        numerology.putObject("destiny").put("title", "운명적 흐름").put("desc", "중요한 선택은 함께 의논하면 좋아요.");
        numerology.putObject("complement").put("title", "보완의 지점").put("desc", "역할을 분명히 하면 시너지가 커질 수 있어요.");

        return root;
    }
}
