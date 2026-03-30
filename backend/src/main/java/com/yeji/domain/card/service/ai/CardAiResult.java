package com.yeji.domain.card.service.ai;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * AI 결과 DTO
 *
 * raw: AI가 내려준 "원본 응답 JSON 전체"를 그대로 담는다
 *   - 예) {"success":true, "validated":true, "type":"eastern", "data":{...}, "errors":null, "latency_ms":0}
 *
 * 이 값을 DB(json/jsonb)에 그대로 저장하면,
 * 프론트에서 aiReading.data.cards / aiReading.data.summary / aiReading.data.lucky 등을 바로 꺼내서 사용 가능.
 */
public record CardAiResult(JsonNode raw) {
}
