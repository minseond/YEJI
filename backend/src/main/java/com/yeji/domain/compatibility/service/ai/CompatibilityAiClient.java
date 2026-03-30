package com.yeji.domain.compatibility.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import reactor.core.publisher.Mono;

import java.util.Map;

public interface CompatibilityAiClient {
    Mono<JsonNode> analyze(Map<String, Object> aiRequestBody);
}
