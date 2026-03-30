package com.yeji.domain.session.controller;

import com.yeji.domain.session.dto.SessionStartRequest;
import com.yeji.domain.session.dto.SessionStartResponse;
import com.yeji.domain.session.service.SessionService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Session API", description = "대화 세션 시작/관리 API (SSE 기반 기능용)")
@RestController
@RequestMapping("/session")
@RequiredArgsConstructor
public class SessionController {

    private final SessionService sessionService;

    @PostMapping("/start")
    @Operation(
            summary = "세션 시작",
            description = "대화 세션을 생성하고 sessionId 및 서비스 목록을 반환합니다."
    )
    public ResponseEntity<ApiResponse<SessionStartResponse>> start(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestBody(required = false) SessionStartRequest request
    ) {
        if (request != null && request.user_id() != null && !request.user_id().equals(authUser.getUserId())) {
            throw new RuntimeException("user_id가 로그인 정보와 일치하지 않습니다.");
        }
        String char1 = (request != null && request.char1_code() != null) ? request.char1_code() : null;
        String char2 = (request != null && request.char2_code() != null) ? request.char2_code() : null;

        return ResponseEntity.ok(
                ApiResponse.ok(sessionService.start(authUser.getUserId(), char1, char2)));
    }
}
