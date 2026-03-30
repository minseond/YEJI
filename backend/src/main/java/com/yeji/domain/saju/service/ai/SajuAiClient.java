package com.yeji.domain.saju.service.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.yeji.domain.saju.service.ai.dto.SajuAiRequest;

public interface SajuAiClient {
    //AI 분석 수행
    //현재는 Stub 구현체 동작으로 넣어뒀고
    //실제 AI 연동 시 이 요청 DTO를 그대로 AI 서버에 전송

    JsonNode analyze(SajuAiRequest request);
}
