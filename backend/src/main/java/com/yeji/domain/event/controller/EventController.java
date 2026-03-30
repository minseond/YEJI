package com.yeji.domain.event.controller;

import com.yeji.domain.event.dto.EventParticipateResponse;
import com.yeji.domain.event.dto.EventResponse;
import com.yeji.domain.event.service.EventService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/events")
@RequiredArgsConstructor
@Tag(name = "Event", description = "이벤트(출석, 뽑기) 관련 API")
public class EventController {

    private final EventService eventService;

    @GetMapping({"", "/"})
    @Operation(summary = "진행 중인 이벤트 목록 조회", description = "현재 참여 가능한 이벤트 목록과 나의 오늘 참여 현황을 조회합니다.")
    public ApiResponse<List<EventResponse>> getEvents(@AuthenticationPrincipal AuthUser authUser) {
        Long userId = (authUser != null) ? authUser.getUserId() : null;
        if (userId == null) {
            throw new IllegalArgumentException("로그인이 필요합니다."); // GlobalExceptionHandler에서 처리됨
        }

        // 수정됨: ApiResponse.ok() 사용
        return ApiResponse.ok(eventService.getActiveEvents(userId));
    }

    @PostMapping("/{eventId}/participate")
    @Operation(summary = "이벤트 참여하기", description = "출석체크 또는 뽑기 이벤트에 참여하여 보상을 받습니다.", security = @SecurityRequirement(name = "bearerAuth"))
    public ApiResponse<EventParticipateResponse> participate(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable Long eventId) {

        // 수정됨: ApiResponse.ok() 사용
        return ApiResponse.ok(eventService.participate(authUser.getUserId(), eventId));
    }
}