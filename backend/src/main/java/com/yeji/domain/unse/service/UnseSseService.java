package com.yeji.domain.unse.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * ⚠️ LEGACY
 *
 * 이전 구현에서 SseEmitter 생성/중계를 별도 서비스로 분리했으나,
 * 현재는 UnseFlowService가 SSE 스트리밍을 일괄 담당합니다.
 *
 * 기존 코드가 컴파일 에러 없이 남아있도록 최소 래퍼만 유지합니다.
 */
@Service
@RequiredArgsConstructor
public class UnseSseService {

    private final UnseFlowService unseFlowService;

    /**
     * (레거시) UnseFlowService로 위임
     */
    public SseEmitter openStream(String backendSessionId, Long userId, String message) {
        return unseFlowService.openChatTurnStream(backendSessionId, userId, message);
    }
}
