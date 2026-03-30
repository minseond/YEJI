package com.yeji.domain.compatibility.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

@Slf4j
@Component
@Profile({"dev", "prod"})
@Primary
@RequiredArgsConstructor
public class RealCompatibilityAiClient implements CompatibilityAiClient {

    private final WebClient.Builder webClientBuilder;
    private final FallbackCompatibilityAiClient fallbackClient;

    @Value("${ai.yeji.base-url}")
    private String baseUrl;

    // yml에 ai.yeji.fortune.compatibility-endpoint 추가 권장
    @Value("${ai.yeji.fortune.compatibility-endpoint:/v1/fortune/compatibility}")
    private String compatibilityEndpoint;

    @Value("${ai.yeji.fortune.timeout-ms:300000}")
    private long timeoutMs;

    @Override
    public Mono<JsonNode> analyze(Map<String, Object> aiRequestBody) {
        WebClient wc = webClientBuilder
                .baseUrl(baseUrl)
                .build();

        return wc.post()
                .uri(compatibilityEndpoint)
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .bodyValue(aiRequestBody)
                .retrieve()
                .bodyToMono(JsonNode.class)
                .timeout(Duration.ofMillis(timeoutMs))
                .doOnSubscribe(s -> log.info("[COMPAT][AI-REQ] endpoint={} timeoutMs={} bodyKeys={}",
                        compatibilityEndpoint, timeoutMs, aiRequestBody.keySet()))
                .doOnSuccess(r -> log.info("[COMPAT][AI-OK] endpoint={}", compatibilityEndpoint))
                .onErrorResume(ex -> {
                    if (ex instanceof WebClientResponseException wex) {
                        log.warn("[COMPAT][AI-ERR] status={} body={}", wex.getRawStatusCode(), safeBody(wex));
                    } else {
                        log.warn("[COMPAT][AI-ERR] {}", ex.toString());
                    }
                    // 장애/타임아웃/4xx/5xx 모두 fallback (Swagger 스키마 형태)
                    return Mono.just(fallbackClient.fallback());
                });
    }

    private String safeBody(WebClientResponseException ex) {
        try {
            String b = ex.getResponseBodyAsString();
            if (b == null) return "";
            return b.length() > 1500 ? b.substring(0, 1500) + "..." : b;
        } catch (Exception ignore) {
            return "";
        }
    }
}
