package com.yeji.domain.unse.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import reactor.core.publisher.Flux;

public interface UnseAiClient {

    //시작 (그리팅)
    JsonNode greeting(String birthDate, String birthTime, String category, String char1Code, String char2Code);

    //턴 단위 티키타카
    Flux<JsonNode> streamChatTurn(String sessionId, String message, String char1Code, String char2Code, boolean extendTurn);

    //최종 결과조회
    JsonNode getChatSummary(String aiSessionId, String type, String category);

    // 정적 운세 분석 (오늘의 운세 용)
    JsonNode getAnalysis(String fortuneId, String type, String category, String persona, boolean force);
}
