package com.yeji.domain.unse.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Real AI Client (Dev/Prod)
 * - POST /v1/fortune/chat/greeting
 * - POST /v1/fortune/chat/turn (SSE)
 * - GET  /v1/fortune/chat/summary/{session_id}?type=...&category=...
 */
@Slf4j
@Component
@Profile({"prod", "dev"})
@Primary
@RequiredArgsConstructor
public class RealUnseAiClient implements UnseAiClient {

    private final ObjectMapper objectMapper;
    private final FallbackUnseAiClient fallback;

    // ====== application.yml @Value 주입 ======
    @Value("${ai.yeji.base-url}")
    private String baseUrl;

    @Value("${ai.yeji.fortune.chat-greeting-endpoint}")
    private String chatGreetingEndpoint;

    @Value("${ai.yeji.fortune.chat-turn-endpoint}")
    private String chatTurnEndpoint;

    @Value("${ai.yeji.fortune.chat-summary-endpoint}")
    private String chatSummaryEndpoint;

    @Value("${ai.yeji.fortune.eastern-endpoint}")
    private String easternEndpoint;

    @Value("${ai.yeji.fortune.western-endpoint}")
    private String westernEndpoint;

    // 필요시 조절
    private static final Duration JSON_TIMEOUT = Duration.ofSeconds(300);
    private static final Duration SSE_RESPONSE_TIMEOUT = Duration.ofSeconds(300);

    /**
     * WebClient를 이 클래스에서 직접 생성(설정 클래스 불필요)
     * - baseUrl은 @Value로 주입되므로 실제 호출 시점에 lazy 생성
     */
    private WebClient webClient;

    private WebClient client() {
        if (webClient != null) return webClient;

        // 메모리/응답크기 제한 조절(필요시)
        ExchangeStrategies strategies = ExchangeStrategies.builder()
                .codecs(cfg -> cfg.defaultCodecs().maxInMemorySize(4 * 1024 * 1024))
                .build();

        HttpClient httpClient = HttpClient.create()
                .responseTimeout(SSE_RESPONSE_TIMEOUT);

        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .exchangeStrategies(strategies)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();

        return this.webClient;
    }

    @Override
    public JsonNode greeting(String birthDate, String birthTime, String category, String char1Code, String char2Code) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("birth_date", birthDate);
        body.put("birth_time", birthTime);
        body.put("category", category != null ? category.toUpperCase() : "GENERAL");
        body.put("char1_code", char1Code);
        body.put("char2_code", char2Code);

        //ai쪽 요청 로그 (birth_date check)
        log.info("[UNSE][AI-REQ][START] payload={}", body);
        return client().post()
                .uri(chatGreetingEndpoint)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(JSON_TIMEOUT)
                .onErrorResume(e -> {
                    log.error("[UNSE][AI-ERR][START] Greeting failed", e);
                    return Mono.just(fallback.greeting(birthDate, birthTime, category, char1Code, char2Code));
                })
                .block();
    }

    @Override
    public Flux<JsonNode> streamChatTurn(
            String aiSessionId,
            String message,
            String char1Code,
            String char2Code,
            boolean extendTurn
    ) {
        Map<String, Object> body = new LinkedHashMap<>();

        if (StringUtils.hasText(aiSessionId)) body.put("session_id", aiSessionId);
        body.put("message", message == null ? "" : message);
        // body.put("char1_code", char1Code); // Not in latest spec
        // body.put("char2_code", char2Code); // Not in latest spec
        // body.put("extend_turn", extendTurn); // Not in latest spec

        log.info("[UNSE][AI-REQ][CONTINUE] session_id={} message={} stream=false", aiSessionId, message);

        Flux<String> raw = client().post()
                .uri(uriBuilder -> uriBuilder
                        .path(chatTurnEndpoint)
                        .queryParam("stream", false)
                        .build())
                .header(HttpHeaders.ACCEPT, MediaType.TEXT_EVENT_STREAM_VALUE)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(body)
                .retrieve()
                .bodyToFlux(String.class);

        return parseSseToJson(raw)
                .onErrorResume(e -> {
                    log.error("[UNSE][AI-ERR][CONTINUE] Chat turn failed", e);
                    return fallback.streamChatTurn(aiSessionId, message, char1Code, char2Code, extendTurn);
                });
    }

    @Override
    public JsonNode getChatSummary(String aiSessionId, String type, String category) {
        log.info("[UNSE][AI-REQ][SUMMARY] session_id={} type={} category={}", aiSessionId, type, category);

        // 반드시 /summary/{session_id} 형태
        String path = normalizeSummaryPath(chatSummaryEndpoint, aiSessionId);

        return client().get()
                .uri(uriBuilder -> uriBuilder
                        .path(path)
                        .queryParam("type", type)
                        .queryParam("category", category)
                        .build()
                )
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(JSON_TIMEOUT)
                .onErrorResume(e -> {
                    log.error("[UNSE][AI-ERR][SUMMARY] Failed to get summary", e);
                    return Mono.just(fallback.getChatSummary(aiSessionId, type, category));
                })
                .block();
    }


    private String normalizeSummaryPath(String base, String sessionId) {
        if (base == null) base = "";
        if (sessionId == null) sessionId = "";
        if (base.endsWith("/")) return base + sessionId;
        return base + "/" + sessionId;
    }

    /**
     * SSE parser:
     * - event: xxx
     * - data: {...json...}
     * - empty line -> flush event
     * 서버가 chunk로 보낼 수 있어 "\n" 단위 split 처리 포함.
     */
    private Flux<JsonNode> parseSseToJson(Flux<String> raw) {
        return Flux.create(sink -> {
            StringBuilder dataBuf = new StringBuilder();
            AtomicReference<String> eventName = new AtomicReference<>(null);

            raw.subscribe(
                    chunk -> {
                        if (chunk == null) return;
                        log.info("[UNSE][AI-RES][SSE-CHUNK] {}", chunk);

                        String[] lines = chunk.split("\\r?\\n");
                        for (String line : lines) {
                            String s = line;

                            // 이벤트 경계(빈 줄)
                            if (!StringUtils.hasText(s)) {
                                emitOne(sink, eventName.get(), dataBuf);
                                eventName.set(null);
                                continue;
                            }

                            if (s.startsWith("event:")) {
                                eventName.set(s.substring("event:".length()).trim());
                                continue;
                            }

                            if (s.startsWith("data:")) {
                                String payload = s.substring("data:".length()).trim();
                                if (dataBuf.length() > 0) dataBuf.append("\n");
                                dataBuf.append(payload);
                                continue;
                            }

                            // 일부 구현은 data: 없이 JSON을 바로 줄 수 있음
                            if (s.startsWith("{") || s.startsWith("[")) {
                                if (dataBuf.length() > 0) dataBuf.append("\n");
                                dataBuf.append(s.trim());
                            }
                        }
                    },
                    sink::error,
                    () -> {
                        emitOne(sink, eventName.get(), dataBuf);
                        sink.complete();
                    }
            );
        });
    }

    private void emitOne(reactor.core.publisher.FluxSink<JsonNode> sink, String event, StringBuilder dataBuf) {
        if (dataBuf == null || dataBuf.length() == 0) return;

        String data = dataBuf.toString().trim();
        dataBuf.setLength(0);

        try {
            JsonNode node;

            if (data.startsWith("{") || data.startsWith("[")) {
                node = objectMapper.readTree(data);

                // event가 따로 왔는데 payload에 event 필드가 없으면 보강
                if (event != null && node.isObject() && node.get("event") == null) {
                    ((ObjectNode) node).put("event", event);
                }
            } else {
                ObjectNode obj = objectMapper.createObjectNode();
                obj.put("event", event == null ? "message" : event);
                obj.put("data", data);
                node = obj;
            }

            sink.next(node);
            log.info("[UNSE][AI-RES][SSE-PARSED] {}", node);

        } catch (Exception ex) {
            ObjectNode obj = objectMapper.createObjectNode();
            obj.put("event", event == null ? "message" : event);
            obj.put("data", data);
            obj.put("parse_error", ex.getClass().getSimpleName());
            log.error("[UNSE][AI-ERR][SSE-PARSE] Data: {} Error: {}", data, ex.getMessage());
            sink.next(obj);
        }
    }

    @Override
    public JsonNode getAnalysis(String fortuneId, String type, String category, String persona, boolean force) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("fortune_id", fortuneId);
        body.put("fortune_type", type);
        body.put("category", category != null ? category.toUpperCase() : "GENERAL");
        body.put("persona", persona);

        log.info("[UNSE][AI-REQ][getAnalysis] force={} body={}", force, body);

        try {
            JsonNode response = client()
                    .post()
                    .uri(uriBuilder -> uriBuilder
                            .path("/v1/fortune/quick-summary")
                            .queryParam("force", force)
                            .build()
                    )
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .timeout(JSON_TIMEOUT)
                    .block();

            log.info("[UNSE][AI-RES][getAnalysis] Response: {}", response);
            return response;

        } catch (Exception e) {
            log.error("[UNSE][AI-ERR][getAnalysis] Failed. fortuneId={}, type={}, category={}, force={}, error={}",
                    fortuneId, type, category, force, e.getMessage());
            return fallback.getAnalysis(fortuneId, type, category, persona, force);
        }
    }
}
