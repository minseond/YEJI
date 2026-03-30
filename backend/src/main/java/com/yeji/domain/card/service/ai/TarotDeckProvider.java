package com.yeji.domain.card.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicReference;

@Slf4j
@Component
@Profile({"dev", "prod"})
@RequiredArgsConstructor
public class TarotDeckProvider {

    private final ObjectMapper objectMapper;

    @Value("${ai.yeji.base-url}")
    private String baseUrl;

    private static final Duration TIMEOUT = Duration.ofSeconds(20);

    private final AtomicReference<JsonNode> cachedDeck = new AtomicReference<>();
    private WebClient webClient;

    private WebClient client() {
        if (webClient != null) return webClient;

        ExchangeStrategies strategies = ExchangeStrategies.builder()
                .codecs(cfg -> cfg.defaultCodecs().maxInMemorySize(4 * 1024 * 1024))
                .build();

        HttpClient httpClient = HttpClient.create().responseTimeout(TIMEOUT);

        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .exchangeStrategies(strategies)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();

        return this.webClient;
    }

    /** 필요 시 1회 호출 후 캐시 */
    public JsonNode getDeck() {
        JsonNode deck = cachedDeck.get();
        if (deck != null) return deck;

        JsonNode fetched = client().get()
                .uri("/v1/fortune/tarot/deck")
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(TIMEOUT)
                .block();

        if (fetched == null || !fetched.has("cards")) {
            throw new IllegalStateException("Tarot deck fetch failed or invalid response");
        }

        cachedDeck.compareAndSet(null, fetched);
        log.info("[CARD][TAROT-DECK] cached. total={}", fetched.path("total").asInt());
        return fetched;
    }

    /**
     * 우리 cardCode(int 0~77)를 AI 요청용 카드 객체로 변환
     * - major: {major: "HANGED_MAN", orientation: "UPRIGHT"}
     * - minor: {suit: "CUPS", rank: "ACE", orientation: "UPRIGHT"}
     */
    public ResolvedTarotCard resolveByCardCode(int cardCode, String orientation) {
        JsonNode deck = getDeck();
        JsonNode cards = deck.get("cards");

        if (cardCode < 0 || cardCode > 77) {
            throw new IllegalArgumentException("Tarot cardCode must be 0..77, got " + cardCode);
        }

        // 0~21 : major number 매칭
        if (cardCode <= 21) {
            for (JsonNode c : cards) {
                if ("major".equals(c.path("type").asText()) && c.path("number").asInt(-1) == cardCode) {
                    return ResolvedTarotCard.major(c.path("code").asText(), orientation);
                }
            }
            throw new IllegalStateException("Major tarot not found for number=" + cardCode);
        }

        // 22~77 : minorIndex로 매칭 (minor 목록 순서대로)
        int minorIndex = cardCode - 22;
        int seen = 0;
        for (JsonNode c : cards) {
            if ("minor".equals(c.path("type").asText())) {
                if (seen == minorIndex) {
                    String suit = c.path("suit").asText();
                    String rank = c.path("rank").asText();
                    if (suit.isEmpty() || rank.isEmpty()) {
                        throw new IllegalStateException("Minor tarot missing suit/rank for code=" + c.path("code").asText());
                    }
                    return ResolvedTarotCard.minor(suit, rank, orientation);
                }
                seen++;
            }
        }
        throw new IllegalStateException("Minor tarot not found for minorIndex=" + minorIndex);
    }

    public record ResolvedTarotCard(
            boolean isMajor,
            String major,
            String suit,
            String rank,
            String orientation
    ) {
        public static ResolvedTarotCard major(String major, String orientation) {
            return new ResolvedTarotCard(true, major, null, null, orientation);
        }
        public static ResolvedTarotCard minor(String suit, String rank, String orientation) {
            return new ResolvedTarotCard(false, null, suit, rank, orientation);
        }
    }
}
