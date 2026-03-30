package com.yeji.domain.card.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.card.entity.CardCategory;
import com.yeji.domain.card.entity.CardSelection;
import com.yeji.domain.user.entity.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import reactor.netty.http.client.HttpClient;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Real AI Client - Tarot/Hwatu Reading
 *  - AI 응답 원본(JsonNode) 그대로 반환
 *  - 요청을 byte[]로 보내 Content-Length 고정 (chunked 전송 방지 → nginx/upstream 502 회피)
 *  - 502/503/504 + 네트워크/timeout 재시도
 *  - X-Request-Id로 추적
 */
@Slf4j
@Component
@Profile({"dev", "prod"})
@Primary
@RequiredArgsConstructor
public class RealCardAiClient implements CardAiClient {

    private final ObjectMapper objectMapper;
    private final FallbackCardAiClient fallback;
    private final TarotDeckProvider tarotDeckProvider;

    @Value("${ai.yeji.base-url}")
    private String baseUrl;

    @Value("${ai.yeji.timeout-ms:180000}")
    private long timeoutMs;

    @Value("${ai.yeji.fortune.tarot-reading-endpoint:/v1/fortune/tarot/reading}")
    private String tarotReadingEndpoint;

    @Value("${ai.yeji.fortune.hwatu-reading-endpoint:/v1/fortune/hwatu/reading}")
    private String hwatuReadingEndpoint;

    @Value("${ai.yeji.fortune.graceful:true}")
    private boolean graceful;

    @Value("${ai.yeji.retry.max-attempts:2}")
    private int retryMaxAttempts;

    @Value("${ai.yeji.retry.backoff-ms:250}")
    private long retryBackoffMs;

    private WebClient webClient;

    private Duration timeout() {
        long ms = Math.max(timeoutMs, 1000);
        return Duration.ofMillis(ms);
    }

    private WebClient client() {
        if (webClient != null) return webClient;

        ExchangeStrategies strategies = ExchangeStrategies.builder()
                .codecs(cfg -> cfg.defaultCodecs().maxInMemorySize(4 * 1024 * 1024))
                .build();

        HttpClient httpClient = HttpClient.create()
                .responseTimeout(timeout());

        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .exchangeStrategies(strategies)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();

        log.info("[CARD][AI-CLIENT] baseUrl={} timeoutMs={}", baseUrl, timeout().toMillis());
        return this.webClient;
    }

    // 분석 시작
    @Override
    public CardAiResult reading(User user, CardCategory category, String question, List<CardSelection> selections) {
        final String endpoint = (category == CardCategory.HWATU) ? hwatuReadingEndpoint : tarotReadingEndpoint;
        final String requestId = UUID.randomUUID().toString();
        final long t0 = System.currentTimeMillis();

        try {
            Map<String, Object> body = buildRequestBody(category, question, selections);

            final String bodyJson = objectMapper.writeValueAsString(body);
            final String bodyHash = sha256Hex(bodyJson);

            int totalAttempts = Math.max(1, retryMaxAttempts);

            for (int attempt = 1; attempt <= totalAttempts; attempt++) {
                long attemptT0 = System.currentTimeMillis();

                log.info("[CARD][AI-REQ] requestId={} attempt={}/{} category={} cards={} endpoint={} graceful={} timeoutMs={} bodyHash={}",
                        requestId, attempt, totalAttempts, category,
                        selections != null ? selections.size() : 0,
                        endpoint, graceful, timeout().toMillis(), bodyHash);

                log.info("[CARD][AI-REQ-BODY] requestId={} {}", requestId, bodyJson);

                try {
                    JsonNode response = callAi(endpoint, body, requestId, t0);

                    if (response == null) {
                        throw new RuntimeException("AI null response");
                    }

                    log.info("[CARD][AI-RESP] requestId={} elapsedMs={} attemptElapsedMs={} success (rawJson)",
                            requestId,
                            System.currentTimeMillis() - t0,
                            System.currentTimeMillis() - attemptT0);

                    return new CardAiResult(response);

                } catch (Exception e) {
                    long elapsed = System.currentTimeMillis() - t0;
                    long attemptElapsed = System.currentTimeMillis() - attemptT0;

                    boolean retryable = isRetryable(e);
                    boolean last = (attempt == totalAttempts);

                    if (!last && retryable) {
                        log.warn("[CARD][AI-RETRY] requestId={} elapsedMs={} attemptElapsedMs={} attempt={}/{} reason={} - retrying after {}ms",
                                requestId, elapsed, attemptElapsed, attempt, totalAttempts, shortErr(e), retryBackoffMs);
                        sleepQuietly(retryBackoffMs);
                        continue;
                    }

                    log.error("[CARD][AI-ERR] requestId={} elapsedMs={} attempt={}/{} retryable={} err={} - using fallback",
                            requestId, elapsed, attempt, totalAttempts, retryable, shortErr(e), e);

                    return fallback.reading(user, category, question, selections);
                }
            }

            return fallback.reading(user, category, question, selections);

        } catch (Exception e) {
            log.error("[CARD][AI-ERR-OUTER] requestId={} elapsedMs={} err={} - using fallback",
                    requestId, System.currentTimeMillis() - t0, shortErr(e), e);
            return fallback.reading(user, category, question, selections);
        }
    }

    private JsonNode callAi(String endpoint, Map<String, Object> body, String requestId, long t0) {
        // chunked 방지: 요청 바디를 byte[]로 만들어 Content-Length를 고정
        final byte[] payloadBytes;
        try {
            payloadBytes = objectMapper.writeValueAsBytes(body);
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize request body", e);
        }

        // 최종 URL 로그
        String finalUrl = baseUrl + endpoint + "?graceful=" + graceful;
        log.info("[CARD][AI-URL] requestId={} {}", requestId, finalUrl);

        return client().post()
                .uri(uriBuilder -> uriBuilder
                        .path(endpoint)
                        .queryParam("graceful", graceful)
                        .build())
                .header("X-Request-Id", requestId)
                // gzip 협상 꼬임 방지(필요 없으면 지워도 됨)
                .header("Accept-Encoding", "identity")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .contentLength(payloadBytes.length)
                .bodyValue(payloadBytes)
                .retrieve()
                .onStatus(
                        status -> status.is4xxClientError() || status.is5xxServerError(),
                        res -> res.bodyToMono(String.class).defaultIfEmpty("")
                                .map(msg -> {
                                    int code = res.statusCode().value();
                                    log.error("[CARD][AI-HTTP-ERR] requestId={} elapsedMs={} status={} body={}",
                                            requestId, System.currentTimeMillis() - t0, res.statusCode(), msg);
                                    return new CardAiHttpException(code, msg);
                                })
                )
                .bodyToMono(JsonNode.class)
                .doOnSubscribe(s -> log.info("[CARD][AI-SUB] requestId={} elapsedMs={} subscribed", requestId, System.currentTimeMillis() - t0))
                .doOnSuccess(r -> log.info("[CARD][AI-SUC] requestId={} elapsedMs={} received", requestId, System.currentTimeMillis() - t0))
                .doOnError(e -> log.error("[CARD][AI-ERR-DETAIL] requestId={} elapsedMs={} err={}",
                        requestId, System.currentTimeMillis() - t0, shortErr(e)))
                .timeout(timeout())
                .block();
    }

    private boolean isRetryable(Throwable e) {
        Throwable cur = e;
        while (cur != null) {
            if (cur instanceof CardAiHttpException ex) {
                int code = ex.getStatusCode();
                return code == 502 || code == 503 || code == 504;
            }
            if (cur instanceof WebClientRequestException) return true;

            String name = cur.getClass().getName();
            if (name.contains("TimeoutException")) return true;
            if (name.contains("ReadTimeoutException")) return true;

            cur = cur.getCause();
        }
        return false;
    }

    private static void sleepQuietly(long ms) {
        if (ms <= 0) return;
        try {
            Thread.sleep(ms);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
        }
    }

    private static String shortErr(Throwable e) {
        if (e == null) return "(null)";
        String msg = e.getMessage();
        if (msg == null) msg = "";
        msg = msg.replace("\n", " ").replace("\r", " ");
        if (msg.length() > 300) msg = msg.substring(0, 300) + "...";
        return e.getClass().getSimpleName() + ":" + msg;
    }

    private static String sha256Hex(String s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] dig = md.digest(s.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(dig.length * 2);
            for (byte b : dig) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return "(sha256-failed)";
        }
    }

    private static class CardAiHttpException extends RuntimeException {
        private final int statusCode;

        CardAiHttpException(int statusCode, String body) {
            super("AI HTTP " + statusCode + (body == null || body.isBlank() ? "" : (" | " + body)));
            this.statusCode = statusCode;
        }

        int getStatusCode() {
            return statusCode;
        }
    }

    private Map<String, Object> buildRequestBody(CardCategory category, String question, List<CardSelection> selections) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("question", question != null ? question : "");

        if (category == CardCategory.HWATU) {
            body.put("category", "HWATU");
            body.put("cards", buildHwatuCardsSwagger(selections));
        } else {
            body.put("cards", buildTarotCardsSwagger(selections));
        }

        return body;
    }

    private List<Map<String, Object>> buildTarotCardsSwagger(List<CardSelection> selections) {
        List<Map<String, Object>> cards = new ArrayList<>();
        if (selections == null) return cards;

        for (CardSelection sel : selections) {
            Map<String, Object> pick = new LinkedHashMap<>();
            pick.put("position", mapTarotPosition(sel.getPosition()));

            String orientation = Boolean.TRUE.equals(sel.getIsReversed()) ? "REVERSED" : "UPRIGHT";
            int cardCode = sel.getCardCode() != null ? sel.getCardCode() : 0;

            TarotDeckProvider.ResolvedTarotCard resolved =
                    tarotDeckProvider.resolveByCardCode(cardCode, orientation);

            Map<String, Object> card = new LinkedHashMap<>();
            card.put("orientation", resolved.orientation());

            if (resolved.isMajor()) {
                card.put("major", resolved.major());
            } else {
                card.put("suit", resolved.suit());
                card.put("rank", resolved.rank());
            }

            pick.put("card", card);
            cards.add(pick);
        }

        return cards;
    }

    private String mapTarotPosition(Integer position) {
        if (position == null) return "PAST";
        return switch (position) {
            case 1 -> "PAST";
            case 2 -> "PRESENT";
            case 3 -> "FUTURE";
            default -> "PAST";
        };
    }

    private List<Map<String, Object>> buildHwatuCardsSwagger(List<CardSelection> selections) {
        List<Map<String, Object>> cards = new ArrayList<>();
        if (selections == null) return cards;

        for (CardSelection sel : selections) {
            Map<String, Object> c = new LinkedHashMap<>();
            c.put("card_code", sel.getCardCode() != null ? sel.getCardCode() : 0);
            c.put("is_reversed", Boolean.TRUE.equals(sel.getIsReversed()));
            c.put("position", sel.getPosition() != null ? sel.getPosition() : 1);
            cards.add(c);
        }

        return cards;
    }
}
