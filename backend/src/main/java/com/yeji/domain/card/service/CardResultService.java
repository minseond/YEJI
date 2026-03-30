package com.yeji.domain.card.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.card.dto.*;
import com.yeji.domain.card.entity.*;
import com.yeji.domain.card.repository.CardResultRepository;
import com.yeji.domain.card.repository.CardSelectionRepository;
import com.yeji.domain.card.service.ai.CardAiClient;
import com.yeji.domain.card.service.ai.CardAiResult;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.service.WalletService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
@Transactional(readOnly = true)
public class CardResultService {

    private static final int TARO_DECK_SIZE = 78;
    private static final int HWATU_DECK_SIZE = 48;

    private final CardResultRepository cardResultRepository;
    private final CardSelectionRepository cardSelectionRepository;
    private final UserRepository userRepository;

    private final CardAiClient cardAiClient;
    private final WalletService walletService;

    private final ObjectMapper objectMapper;

    public CardResultService(
            CardResultRepository cardResultRepository,
            CardSelectionRepository cardSelectionRepository,
            UserRepository userRepository,
            CardAiClient cardAiClient,
            WalletService walletService,
            ObjectMapper objectMapper
    ) {
        this.cardResultRepository = cardResultRepository;
        this.cardSelectionRepository = cardSelectionRepository;
        this.userRepository = userRepository;
        this.cardAiClient = cardAiClient;
        this.walletService = walletService;
        this.objectMapper = objectMapper;
    }

    public CardResultDetailResponse getDetail(Long userId, Long cardResultId) {
        CardResult result = cardResultRepository.findByIdAndUser_Id(cardResultId, userId)
                .orElseThrow(() -> new RuntimeException("카드 결과를 찾을 수 없습니다."));

        List<CardSelectedCardResponse> cards = cardSelectionRepository.findByResultId(cardResultId)
                .stream()
                .map(CardSelectedCardResponse::new)
                .toList();

        return CardResultDetailResponse.of(result, cards, objectMapper);
    }

    public List<CardResultListItemResponse> getHistoryList(Long userId, String category, LocalDate from, LocalDate to) {
        CardCategory cat = (category == null || category.isBlank()) ? null : CardCategory.from(category);

        LocalDateTime fromDt = (from == null) ? null : from.atStartOfDay();
        LocalDateTime toDt = (to == null) ? null : to.plusDays(1).atStartOfDay().minusNanos(1);

        return cardResultRepository.findAllByUserIdWithFilters(userId, cat, fromDt, toDt)
                .stream()
                .map(CardResultListItemResponse::new)
                .toList();
    }

    public CardResultDetailResponse getHistoryDetail(Long userId, Long cardResultId) {
        return getDetail(userId, cardResultId);
    }

    /**
     * 프롬프트/질문을 아예 받지 않음
     * - request.topic(MONEY/LOVE/...)만 받음
     * - AI에는 question 대신 topic string만 전달
     * - DB에는 기존 question 컬럼이 있으면 거기에 topic 값만 저장(스키마 변경 없이)
     */
    @Transactional
    public CardResultDetailResponse createReading(Long userId, CardCreateReadingRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("유저를 찾을 수 없습니다."));

        CardCategory category = CardCategory.from(request.getCategory());
        validateCards(category, request.getCards());

        CardTopic topic = CardTopic.from(request.getTopic());
        String topicCode = topic.name(); // "LOVE" 같은 값

        CardResult savedResult = cardResultRepository.save(
                CardResult.builder()
                        .user(user)
                        .category(category)
                        .question(topicCode)  // 기존 컬럼 재활용: 이제는 topic 코드 저장
                        .aiReading(null)
                        .build()
        );

        List<CardSelection> selections = request.getCards().stream()
                .map(c -> CardSelection.builder()
                        .cardResult(savedResult)
                        .user(user)
                        .cardCode(c.getCardCode())
                        .position(c.getPosition())
                        .isReversed(category == CardCategory.HWATU ? false : Boolean.TRUE.equals(c.getIsReversed()))
                        .build()
                ).toList();

        cardSelectionRepository.saveAll(selections);

        // AI에는 "question" 대신 topicCode만 전달
        CardAiResult ai = cardAiClient.reading(user, category, topicCode, selections);

        String safeJson = toSafeJson(ai == null ? null : ai.raw(), category, topicCode);
        savedResult.updateAiReading(safeJson);

        List<CardSelectedCardResponse> cardResponses = selections.stream()
                .sorted((a, b) -> Integer.compare(a.getPosition(), b.getPosition()))
                .map(CardSelectedCardResponse::new)
                .toList();

        return CardResultDetailResponse.of(savedResult, cardResponses, objectMapper);
    }

    private String toSafeJson(JsonNode raw, CardCategory category, String topicCode) {
        if (raw != null) return raw.toString();

        ObjectNode root = objectMapper.createObjectNode();
        root.put("success", true);
        root.put("validated", false);
        root.put("type", "empty");

        ObjectNode data = root.putObject("data");
        data.put("category", category == null ? "" : category.name().toLowerCase());
        data.put("topic", topicCode == null ? "" : topicCode);
        data.put("message", "AI 응답이 비어 있습니다.");

        root.putNull("errors");
        root.put("latency_ms", 0);
        return root.toString();
    }

    private void validateCards(CardCategory category, List<CardSelectedCardRequest> cards) {
        int expected = (category == CardCategory.HWATU) ? 4 : 3;

        if (cards == null || cards.size() != expected) {
            throw new RuntimeException("카드는 정확히 " + expected + "장이어야 합니다.");
        }

        Set<Integer> positions = new HashSet<>();
        Set<Integer> cardCodes = new HashSet<>();

        int maxCode = (category == CardCategory.HWATU) ? (HWATU_DECK_SIZE - 1) : (TARO_DECK_SIZE - 1);

        for (CardSelectedCardRequest c : cards) {
            if (c.getCardCode() == null || c.getPosition() == null) {
                throw new RuntimeException("카드 정보가 올바르지 않습니다. (cardCode/position 누락)");
            }

            if (c.getCardCode() < 0 || c.getCardCode() > maxCode) {
                throw new RuntimeException(category.name() + " cardCode 범위 오류: 0~" + maxCode + " 여야 합니다.");
            }

            if (!cardCodes.add(c.getCardCode())) {
                throw new RuntimeException("중복된 cardCode가 포함되어 있습니다: " + c.getCardCode());
            }

            if (!positions.add(c.getPosition())) {
                throw new RuntimeException("카드 배치 순서(position)은 중복될 수 없습니다: " + c.getPosition());
            }

            if (category == CardCategory.TARO) {
                if (c.getIsReversed() == null) {
                    throw new RuntimeException("TARO는 isReversed 값이 필요합니다. (true/false)");
                }
            } else {
                if (Boolean.TRUE.equals(c.getIsReversed())) {
                    throw new RuntimeException("HWATU는 isReversed=true를 허용하지 않습니다. (항상 false)");
                }
            }
        }

        Set<Integer> required = (expected == 4) ? Set.of(1, 2, 3, 4) : Set.of(1, 2, 3);
        if (positions.size() != expected || !positions.containsAll(required)) {
            throw new RuntimeException("카드 배치 순서는 1~" + expected + "가 중복 없이 모두 포함되어야 합니다.");
        }
    }
}
