package com.yeji.domain.compatibility.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * 로컬/테스트용 더미 응답 -> AI 불러오지 못하면 이 응답 띄우도록
 * AI Swagger(/v1/fortune/compatibility) 응답 스키마와 동일한 형태를 반환합니다. (wrapper 없음)
 */
@Component
@Profile("!dev & !prod")
@Primary
@RequiredArgsConstructor
public class StubCompatibilityAiClient implements CompatibilityAiClient {

    private final ObjectMapper objectMapper;

    @Override
    public Mono<JsonNode> analyze(Map<String, Object> requestBody) {
        ObjectNode root = objectMapper.createObjectNode();

        ObjectNode score = root.putObject("score");
        score.put("total", 71);
        score.put("east", 32);
        score.put("west", 39);

        root.put("grade", "good");
        root.put("grade_label", "좋은 궁합");
        root.put("score_range", "good");

        ObjectNode message = root.putObject("message");

        ObjectNode east = message.putObject("east");
        ObjectNode eastRel = east.putObject("relationship_dynamics");

        eastRel.putObject("communication")
                .put("desc", "솔직한 대화가 잘 통하는 편이라 오해가 적어요. 중요한 감정은 미루지 말고 즉시 나누는 것이 좋아요.");
        eastRel.putObject("flexibility")
                .put("desc", "서로의 일정과 습관을 존중하며 조정할 수 있어요. 작은 타협을 미리 정해두면 갈등이 줄어요.");
        eastRel.putObject("stability")
                .put("desc", "관계의 기반이 안정적이며 함께하는 시간이 큰 힘이 돼요. 생활 패턴을 맞춰 루틴을 만들면 더 안정됩니다.");
        eastRel.putObject("passion")
                .put("desc", "애정 표현은 꾸준하고 세심한 편이라 신뢰를 줘요. 함께하는 소소한 이벤트로 열정을 유지하세요.");
        eastRel.putObject("growth")
                .put("desc", "상대의 장점을 북돋아주며 함께 성장하려는 의지가 있어요. 목표를 쪼개서 달성해 나가면 성취감이 커져요.");

        ObjectNode eastSum = east.putObject("compatibility_summary");
        eastSum.putArray("keywords").add("동병상련").add("심심상인");
        eastSum.put("desc", "비슷한 경험과 가치가 연결되어 공감대가 튼튼한 조합이에요. 상대의 어려움을 이해하고 함께 해결책을 찾을 수 있어요.");

        ObjectNode west = message.putObject("west");
        ObjectNode zodiac = west.putObject("zodiac");
        ObjectNode aspects = zodiac.putObject("aspects");

        aspects.putObject("moon_resonance")
                .put("title", "정서적 교감")
                .put("desc", "서로의 감정을 민감하게 캐치하며 지지해 주는 편이에요. 감정의 변화는 공유하면 오해를 줄일 수 있어요.");
        aspects.putObject("mercury_communication")
                .put("title", "의사소통 패턴")
                .put("desc", "대화에서 사실을 중시하고 솔루션 지향적이에요. 감정적 사안은 먼저 공감 표현을 하는 연습을 해보세요.");
        aspects.putObject("venus_mars_values")
                .put("title", "애정의 조화")
                .put("desc", "애정 표현과 생활 가치가 자연스럽게 맞물려 있어요. 공동의 취미를 통해 감정적 유대를 강화하세요.");
        aspects.putObject("saturn_stability")
                .put("title", "책임의 무게")
                .put("desc", "책임을 나누는 데 능숙해 장기적으로 믿음이 가요. 큰 결심은 단계별 계획을 세워 실천하세요.");

        ObjectNode numerology = west.putObject("numerology");
        numerology.putObject("life_path")
                .put("title", "인생 여정")
                .put("desc", "삶의 방향이 비슷해 서로의 성취를 응원하기 좋아요. 작은 공동 프로젝트부터 시작해 보세요.");
        numerology.putObject("destiny")
                .put("title", "운명적 흐름")
                .put("desc", "운의 흐름이 서로를 돕는 방향으로 흐를 가능성이 커요. 중요한 선택은 함께 의논해 신중히 결정하세요.");
        numerology.putObject("complement")
                .put("title", "보완의 지점")
                .put("desc", "한쪽의 계획성이 다른 쪽의 창의성을 보완해요. 역할을 분명히 하면 시너지가 커집니다.");

        return Mono.just(root);
    }
}
